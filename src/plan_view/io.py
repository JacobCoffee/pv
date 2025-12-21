"""Plan file I/O operations."""

import json
import sys
from importlib.resources import files
from pathlib import Path

from plan_view.formatting import now_iso
from plan_view.state import recalculate_progress


def load_plan(path: Path) -> dict | None:
    """Load and parse plan.json."""
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
        return None


def save_plan(path: Path, plan: dict) -> None:
    """Save plan.json with updated timestamp."""
    plan["meta"]["updated_at"] = now_iso()
    recalculate_progress(plan)
    path.write_text(json.dumps(plan, indent=2) + "\n")


def load_schema() -> dict:
    """Load the bundled JSON schema."""
    schema_path = files("plan_view").joinpath("plan.schema.json")
    return json.loads(schema_path.read_text())
