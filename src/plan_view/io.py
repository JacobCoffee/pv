"""Plan file I/O operations."""

import json
import sys
from importlib.resources import files
from pathlib import Path

from plan_view.formatting import now_iso
from plan_view.state import SPECIAL_PHASE_IDS, recalculate_progress

# Order for special phases (always sorted last in this order)
SPECIAL_PHASE_ORDER = ["bugs", "ideas", "deferred"]


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


def load_schema() -> dict:
    """Load the bundled JSON schema."""
    schema_path = files("plan_view").joinpath("plan.schema.json")
    return json.loads(schema_path.read_text())
