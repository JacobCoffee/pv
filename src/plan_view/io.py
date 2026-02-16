"""Plan file I/O operations."""

import copy
import json
import sys
import tomllib
from importlib.resources import files
from pathlib import Path

import jsonpatch

from plan_view.formatting import now_iso
from plan_view.state import SPECIAL_PHASE_IDS, recalculate_progress

# Order for special phases (always sorted last in this order)
SPECIAL_PHASE_ORDER = ["bugs", "ideas", "deferred"]

# Config file names to search for
CONFIG_FILES = [".pv.toml", "pyproject.toml"]


def _find_config_file(start_dir: Path | None = None) -> tuple[Path, dict] | None:
    """Find config file by walking up from start_dir to filesystem root.

    Searches for .pv.toml first, then pyproject.toml with [tool.pv] section.
    Returns (config_path, config_dict) or None if not found.
    """
    current = (start_dir or Path.cwd()).resolve()

    while True:
        # Check .pv.toml first (dedicated config file)
        pv_toml = current / ".pv.toml"
        if pv_toml.exists():
            try:
                config = tomllib.loads(pv_toml.read_text())
                return pv_toml, config
            except tomllib.TOMLDecodeError:
                pass  # Invalid TOML, continue searching

        # Check pyproject.toml for [tool.pv] section
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            try:
                data = tomllib.loads(pyproject.read_text())
                if "tool" in data and "pv" in data["tool"]:
                    return pyproject, data["tool"]["pv"]
            except tomllib.TOMLDecodeError:
                pass  # Invalid TOML, continue searching

        # Move to parent directory
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None
        current = parent


def resolve_plan_path(explicit_path: Path | None = None) -> Path:
    """Resolve the plan.json path using config files if no explicit path given.

    Resolution order:
    1. If explicit_path is provided and not the default, use it directly
    2. Search for .pv.toml or pyproject.toml [tool.pv] walking up from cwd
    3. If config found with plan_file setting, resolve relative to config location
    4. Fall back to ./plan.json

    Config file format (.pv.toml or pyproject.toml [tool.pv]):
        plan_file = "path/to/plan.json"  # Relative to config file location
    """
    default_path = Path("plan.json")

    # If user explicitly specified a non-default path, use it
    if explicit_path is not None and explicit_path != default_path:
        return explicit_path

    # Search for config file
    result = _find_config_file()
    if result is None:
        return explicit_path or default_path

    config_path, config = result
    plan_file = config.get("plan_file")

    if plan_file:
        # Resolve relative to config file's directory
        return (config_path.parent / plan_file).resolve()

    # Config exists but no plan_file setting - check for plan.json in config dir
    config_dir_plan = config_path.parent / "plan.json"
    if config_dir_plan.exists():
        return config_dir_plan

    return explicit_path or default_path


def _phase_sort_key(phase: dict) -> tuple[int, int | str]:
    """Sort key for phases: numeric phases first (sorted), then special phases last."""
    phase_id = phase["id"]
    if phase_id in SPECIAL_PHASE_IDS:
        # Special phases come after all numeric phases (group 1)
        # Ordered by SPECIAL_PHASE_ORDER
        try:
            order = SPECIAL_PHASE_ORDER.index(phase_id)
        except ValueError:
            order = len(SPECIAL_PHASE_ORDER)  # Unknown special phases at end
        return (1, order)
    # Numeric phases come first (group 0), sorted by numeric value
    try:
        return (0, int(phase_id))
    except ValueError:
        # Non-numeric, non-special phases: treat as large number
        return (0, 999999)


def _sort_phases(plan: dict) -> None:
    """Sort phases: numeric first (by number), special phases last."""
    plan["phases"] = sorted(plan.get("phases", []), key=_phase_sort_key)


def _ensure_special_phases(plan: dict) -> bool:
    """Ensure bugs and deferred phases exist. Returns True if plan was modified."""
    phases = plan.get("phases", [])
    phase_ids = {p["id"] for p in phases}
    modified = False

    if "deferred" not in phase_ids:
        phases.append(
            {
                "id": "deferred",
                "name": "Deferred",
                "description": "Tasks postponed for later consideration",
                "status": "pending",
                "progress": {"completed": 0, "total": 0, "percentage": 0},
                "tasks": [],
            }
        )
        modified = True

    if "bugs" not in phase_ids:
        phases.append(
            {
                "id": "bugs",
                "name": "Bugs",
                "description": "Tasks identified as bugs requiring fixes",
                "status": "pending",
                "progress": {"completed": 0, "total": 0, "percentage": 0},
                "tasks": [],
            }
        )
        modified = True

    return modified


def load_plan(path: Path, *, auto_migrate: bool = False) -> dict | None:
    """Load and parse plan.json, ensuring special phases exist.

    Args:
        path: Path to the plan.json file.
        auto_migrate: If True, save the plan after adding missing special phases.
    """
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        return None
    try:
        plan = json.loads(path.read_text())
        # Auto-add missing bugs/deferred phases for legacy plans
        if _ensure_special_phases(plan) and auto_migrate:
            save_plan(path, plan)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
        return None
    else:
        return plan


def save_plan(path: Path, plan: dict) -> None:
    """Save plan.json with updated timestamp and sorted phases."""
    plan["meta"]["updated_at"] = now_iso()
    _sort_phases(plan)
    recalculate_progress(plan)
    path.write_text(json.dumps(plan, indent=2) + "\n")
    maybe_periodic_backup(path, plan)


def _rotate_delta_backups(backup_dir: Path, max_deltas: int = 5) -> None:
    """Rotate delta backup files: .delta.1 → .delta.2, etc."""
    for i in range(max_deltas, 0, -1):
        old = backup_dir / f"plan.delta.{i}.json"
        new = backup_dir / f"plan.delta.{i + 1}.json"
        if old.exists():
            if i == max_deltas:
                old.unlink()
            else:
                old.rename(new)


def maybe_periodic_backup(path: Path, plan: dict) -> None:
    """Create periodic delta backups every 15 saves. Never raises."""
    try:
        backup_dir = path.parent / ".claude" / "plan-view"
        if not backup_dir.exists():
            # Use parent's .claude/plan-view if plan is not at project root
            backup_dir = Path(".claude/plan-view")
        backup_dir.mkdir(parents=True, exist_ok=True)

        periodic_path = backup_dir / "periodic.json"

        if periodic_path.exists():
            state = json.loads(periodic_path.read_text())
        else:
            state = {"count": 0, "base": copy.deepcopy(plan)}

        state["count"] += 1

        if state["count"] % 15 == 0:
            # Compare current plan to base (exclude updated_at for meaningful diff)
            base = state["base"]
            if plan != base:
                patch = jsonpatch.make_patch(base, plan)
                patch_list = patch.patch
                if patch_list:
                    _rotate_delta_backups(backup_dir)
                    delta_path = backup_dir / "plan.delta.1.json"
                    delta_path.write_text(json.dumps(patch_list, indent=2) + "\n")
                state["base"] = copy.deepcopy(plan)

        periodic_path.write_text(json.dumps(state, indent=2) + "\n")
    except Exception:  # noqa: BLE001, S110
        pass  # Backup failures must never crash the CLI


def load_schema() -> dict:
    """Load the bundled JSON schema."""
    schema_path = files("plan_view").joinpath("plan.schema.json")
    return json.loads(schema_path.read_text())
