"""Edit commands for modifying plan data."""

import argparse
import contextlib
import shutil
import sys
from pathlib import Path

from plan_view.decorators import require_plan
from plan_view.formatting import VALID_STATUSES, now_iso
from plan_view.io import save_plan
from plan_view.state import (
    find_phase,
    find_task,
    format_phase_suggestions,
    format_task_suggestions,
)


def _is_dry_run(args: argparse.Namespace) -> bool:
    """Check if dry-run mode is enabled."""
    return getattr(args, "dry_run", False)


def _prefix(args: argparse.Namespace) -> str:
    """Return message prefix based on dry-run mode."""
    return "Would:" if _is_dry_run(args) else "✅"


def cmd_init(args: argparse.Namespace) -> None:
    """Create a new plan.json."""
    path = args.file
    if path.exists() and not args.force:
        print(f"Error: {path} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    plan = {
        "meta": {
            "project": args.name,
            "version": "1.0.0",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "business_plan_path": ".claude/BUSINESS_PLAN.md",
        },
        "summary": {
            "total_phases": 2,
            "total_tasks": 0,
            "completed_tasks": 0,
            "overall_progress": 0,
        },
        "phases": [
            {
                "id": "deferred",
                "name": "Deferred",
                "description": "Tasks postponed for later consideration",
                "status": "pending",
                "progress": {"completed": 0, "total": 0, "percentage": 0},
                "tasks": [],
            },
            {
                "id": "99",
                "name": "Bugs",
                "description": "Tasks identified as bugs requiring fixes",
                "status": "pending",
                "progress": {"completed": 0, "total": 0, "percentage": 0},
                "tasks": [],
            },
        ],
    }

    if not _is_dry_run(args):
        save_plan(path, plan)
    if not getattr(args, "quiet", False):
        print(f"{_prefix(args)} Created {path} for '{args.name}'")


@require_plan
def cmd_add_phase(plan: dict, args: argparse.Namespace) -> None:
    """Add a new phase."""
    # Determine next phase ID
    existing_ids = [int(p["id"]) for p in plan["phases"] if p["id"].isdigit()]
    next_id = str(max(existing_ids, default=-1) + 1)

    phase = {
        "id": next_id,
        "name": args.name,
        "description": args.desc or "",
        "status": "pending",
        "progress": {"completed": 0, "total": 0, "percentage": 0},
        "tasks": [],
    }

    plan["phases"].append(phase)
    if not _is_dry_run(args):
        save_plan(args.file, plan)
    if not getattr(args, "quiet", False):
        print(f"{_prefix(args)} Added Phase {next_id}: {args.name}")


@require_plan
def cmd_add_task(plan: dict, args: argparse.Namespace) -> None:
    """Add a new task to a phase."""
    phase = find_phase(plan, args.phase)
    if phase is None:
        print(f"Error: Phase '{args.phase}' not found\n", file=sys.stderr)
        print(format_phase_suggestions(plan), file=sys.stderr)
        sys.exit(1)
    assert phase is not None

    # Determine next task ID (phase.section.task)
    phase_id = phase["id"]
    existing_tasks = phase.get("tasks", [])

    # Find the highest section.task number
    max_section = 0
    max_task = 0
    for t in existing_tasks:
        parts = t["id"].split(".")
        if len(parts) >= 3:
            section = int(parts[1])
            task_num = int(parts[2])
            if section > max_section or (section == max_section and task_num > max_task):
                max_section = section
                max_task = task_num

    # Use section 1 if no tasks exist, otherwise increment task number
    next_id = f"{phase_id}.1.1" if not existing_tasks else f"{phase_id}.{max_section}.{max_task + 1}"

    task = {
        "id": next_id,
        "title": args.title,
        "status": "pending",
        "agent_type": args.agent,
        "depends_on": args.deps.split(",") if args.deps else [],
        "tracking": {},
    }

    phase["tasks"].append(task)
    if not _is_dry_run(args):
        save_plan(args.file, plan)
    if not getattr(args, "quiet", False):
        print(f"{_prefix(args)} Added [{next_id}] {args.title}")


@require_plan
def cmd_set(plan: dict, args: argparse.Namespace) -> None:
    """Set a task field."""
    result = find_task(plan, args.id)
    if result is None:
        print(f"Error: Task '{args.id}' not found\n", file=sys.stderr)
        print(format_task_suggestions(plan), file=sys.stderr)
        sys.exit(1)
    assert result is not None

    _, task = result

    if args.field == "status":
        if args.value not in VALID_STATUSES:
            print(f"Error: Invalid status. Use: {', '.join(VALID_STATUSES)}", file=sys.stderr)
            sys.exit(1)
        task["status"] = args.value
        if args.value == "in_progress":
            task["tracking"]["started_at"] = now_iso()
        elif args.value == "completed":
            task["tracking"]["completed_at"] = now_iso()
    elif args.field == "agent":
        task["agent_type"] = args.value if args.value != "none" else None
    elif args.field == "title":
        task["title"] = args.value
    else:
        print(f"Error: Unknown field '{args.field}'. Use: status, agent, title", file=sys.stderr)
        sys.exit(1)

    if not _is_dry_run(args):
        save_plan(args.file, plan)
    if not getattr(args, "quiet", False):
        print(f"{_prefix(args)} [{args.id}] {args.field} → {args.value}")


def cmd_done(args: argparse.Namespace) -> None:
    """Mark task as completed."""
    args.field = "status"
    args.value = "completed"
    cmd_set(args)


def cmd_start(args: argparse.Namespace) -> None:
    """Mark task as in_progress."""
    args.field = "status"
    args.value = "in_progress"
    cmd_set(args)


def cmd_block(args: argparse.Namespace) -> None:
    """Mark task as blocked."""
    args.field = "status"
    args.value = "blocked"
    cmd_set(args)


def cmd_skip(args: argparse.Namespace) -> None:
    """Mark task as skipped."""
    args.field = "status"
    args.value = "skipped"
    cmd_set(args)


@require_plan
def cmd_defer(plan: dict, args: argparse.Namespace) -> None:
    """Move task to deferred phase, or create a new deferred task if input is not an existing task ID."""
    # Find or create deferred phase
    deferred = find_phase(plan, "deferred")
    if deferred is None:
        deferred = {
            "id": "deferred",
            "name": "Deferred",
            "description": "Tasks postponed for later consideration",
            "status": "pending",
            "progress": {"completed": 0, "total": 0, "percentage": 0},
            "tasks": [],
        }
        plan["phases"].append(deferred)

    # Generate next ID for deferred phase
    existing_tasks = deferred.get("tasks", [])
    assert isinstance(existing_tasks, list)
    max_task = 0
    for t in existing_tasks:
        assert isinstance(t, dict)
        parts = str(t["id"]).split(".")
        if len(parts) >= 3:
            with contextlib.suppress(ValueError):
                max_task = max(max_task, int(parts[2]))
    new_id = f"deferred.1.{max_task + 1}"

    # Get defer reason if provided (only store non-empty strings)
    defer_reason = getattr(args, "reason", None)
    if defer_reason and not defer_reason.strip():
        defer_reason = None

    # Try to find existing task to move
    result = find_task(plan, args.id)
    if result is not None:
        # Move existing task to deferred
        old_phase, task = result
        old_phase["tasks"].remove(task)
        old_id = task["id"]
        task["id"] = new_id
        # Add defer reason to tracking if provided
        if defer_reason:
            tracking = task["tracking"]
            assert isinstance(tracking, dict)
            tracking["defer_reason"] = defer_reason
        task_list = deferred["tasks"]
        assert isinstance(task_list, list)
        task_list.append(task)
        if not _is_dry_run(args):
            save_plan(args.file, plan)
        if not getattr(args, "quiet", False):
            print(f"{_prefix(args)} [{old_id}] → [{new_id}] (deferred)")
    else:
        # Create new deferred task with input as title
        tracking: dict = {}
        if defer_reason:
            tracking["defer_reason"] = defer_reason
        task = {
            "id": new_id,
            "title": args.id,  # Use input as title
            "status": "pending",
            "agent_type": None,
            "depends_on": [],
            "tracking": tracking,
        }
        task_list = deferred["tasks"]
        assert isinstance(task_list, list)
        task_list.append(task)
        if not _is_dry_run(args):
            save_plan(args.file, plan)
        if not getattr(args, "quiet", False):
            print(f"{_prefix(args)} Added [{new_id}] {args.id} (deferred)")


@require_plan
def cmd_bug(plan: dict, args: argparse.Namespace) -> None:
    """Move task to bugs phase, or create a new bug if input is not an existing task ID."""
    # Find or create bugs phase
    bugs = find_phase(plan, "99")
    if bugs is None:
        bugs = {
            "id": "99",
            "name": "Bugs",
            "description": "Tasks identified as bugs requiring fixes",
            "status": "pending",
            "progress": {"completed": 0, "total": 0, "percentage": 0},
            "tasks": [],
        }
        plan["phases"].append(bugs)

    # Generate next ID for bugs phase
    existing_tasks = bugs.get("tasks", [])
    assert isinstance(existing_tasks, list)
    max_task = 0
    for t in existing_tasks:
        assert isinstance(t, dict)
        parts = str(t["id"]).split(".")
        if len(parts) >= 3:
            with contextlib.suppress(ValueError):
                max_task = max(max_task, int(parts[2]))
    new_id = f"99.1.{max_task + 1}"

    # Try to find existing task to move
    result = find_task(plan, args.id)
    if result is not None:
        # Move existing task to bugs
        old_phase, task = result
        old_phase["tasks"].remove(task)
        old_id = task["id"]
        task["id"] = new_id
        task_list = bugs["tasks"]
        assert isinstance(task_list, list)
        task_list.append(task)
        if not _is_dry_run(args):
            save_plan(args.file, plan)
        if not getattr(args, "quiet", False):
            print(f"{_prefix(args)} [{old_id}] → [{new_id}] (bug)")
    else:
        # Create new bug task with input as title
        task = {
            "id": new_id,
            "title": args.id,  # Use input as title
            "status": "pending",
            "agent_type": None,
            "depends_on": [],
            "tracking": {},
        }
        task_list = bugs["tasks"]
        assert isinstance(task_list, list)
        task_list.append(task)
        if not _is_dry_run(args):
            save_plan(args.file, plan)
        if not getattr(args, "quiet", False):
            print(f"{_prefix(args)} Added [{new_id}] {args.id} (bug)")


@require_plan
def cmd_idea(plan: dict, args: argparse.Namespace) -> None:
    """Move task to ideas phase, or create a new idea if input is not an existing task ID."""
    # Find or create ideas phase
    ideas = find_phase(plan, "ideas")
    if ideas is None:
        ideas = {
            "id": "ideas",
            "name": "Ideas",
            "description": "Tasks stored as future ideas or concepts",
            "status": "pending",
            "progress": {"completed": 0, "total": 0, "percentage": 0},
            "tasks": [],
        }
        plan["phases"].append(ideas)

    # Generate next ID for ideas phase
    existing_tasks = ideas.get("tasks", [])
    assert isinstance(existing_tasks, list)
    max_task = 0
    for t in existing_tasks:
        assert isinstance(t, dict)
        parts = str(t["id"]).split(".")
        if len(parts) >= 3:
            with contextlib.suppress(ValueError):
                max_task = max(max_task, int(parts[2]))
    new_id = f"ideas.1.{max_task + 1}"

    # Try to find existing task to move
    result = find_task(plan, args.id)
    if result is not None:
        # Move existing task to ideas
        old_phase, task = result
        old_phase["tasks"].remove(task)
        old_id = task["id"]
        task["id"] = new_id
        task_list = ideas["tasks"]
        assert isinstance(task_list, list)
        task_list.append(task)
        if not _is_dry_run(args):
            save_plan(args.file, plan)
        if not getattr(args, "quiet", False):
            print(f"{_prefix(args)} [{old_id}] → [{new_id}] (idea)")
    else:
        # Create new idea task with input as title
        task = {
            "id": new_id,
            "title": args.id,  # Use input as title
            "status": "pending",
            "agent_type": None,
            "depends_on": [],
            "tracking": {},
        }
        task_list = ideas["tasks"]
        assert isinstance(task_list, list)
        task_list.append(task)
        if not _is_dry_run(args):
            save_plan(args.file, plan)
        if not getattr(args, "quiet", False):
            print(f"{_prefix(args)} Added [{new_id}] {args.id} (idea)")


@require_plan
def cmd_rm(plan: dict, args: argparse.Namespace) -> None:
    """Remove a phase or task."""
    if args.type == "task":
        result = find_task(plan, args.id)
        if result is None:
            print(f"Error: Task '{args.id}' not found\n", file=sys.stderr)
            print(format_task_suggestions(plan), file=sys.stderr)
            sys.exit(1)
        assert result is not None
        phase, task = result
        phase["tasks"].remove(task)
        if not _is_dry_run(args):
            save_plan(args.file, plan)
        if not getattr(args, "quiet", False):
            print(f"{_prefix(args)} Removed task [{args.id}]")

    else:  # args.type == "phase" (argparse enforces this)
        phase = find_phase(plan, args.id)
        if phase is None:
            print(f"Error: Phase '{args.id}' not found\n", file=sys.stderr)
            print(format_phase_suggestions(plan), file=sys.stderr)
            sys.exit(1)
        assert phase is not None
        plan["phases"].remove(phase)
        if not _is_dry_run(args):
            save_plan(args.file, plan)
        if not getattr(args, "quiet", False):
            print(f"{_prefix(args)} Removed phase {args.id}")


def _rotate_backups(backup_dir: Path, plan_name: str, max_backups: int = 5) -> None:
    """Rotate backup files: .json.1 → .json.2, etc. Deletes oldest if at max."""
    for i in range(max_backups, 0, -1):
        old = backup_dir / f"{plan_name}.json.{i}"
        new = backup_dir / f"{plan_name}.json.{i + 1}"
        if old.exists():
            if i == max_backups:
                old.unlink()  # Delete oldest
            else:
                old.rename(new)


def _compact_task(task: dict) -> bool:
    """Strip completed task to minimal fields. Returns True if modified."""
    keep = {"id", "title", "status", "tracking"}
    removed = [k for k in list(task.keys()) if k not in keep]
    for key in removed:
        del task[key]

    # Keep only completed_at in tracking
    modified = bool(removed)
    if task.get("tracking"):
        completed_at = task["tracking"].get("completed_at")
        old_tracking = task["tracking"]
        task["tracking"] = {"completed_at": completed_at} if completed_at else {}
        if task["tracking"] != old_tracking:
            modified = True

    return modified


@require_plan
def cmd_compact(plan: dict, args: argparse.Namespace) -> None:
    """Backup plan and compact completed tasks to minimal fields."""
    plan_path = Path(args.file)
    max_backups = getattr(args, "max_backups", 5)

    # 1. Create backup directory and rotate existing backups
    backup_dir = Path(".claude/plan-view")
    backup_dir.mkdir(parents=True, exist_ok=True)

    plan_name = plan_path.stem  # "plan" from "plan.json"
    _rotate_backups(backup_dir, plan_name, max_backups)

    # 2. Save current plan as .json.1
    backup_path = backup_dir / f"{plan_name}.json.1"
    shutil.copy2(plan_path, backup_path)

    # 3. Compact completed tasks
    compacted = 0
    for phase in plan["phases"]:
        for task in phase["tasks"]:
            if task["status"] == "completed" and _compact_task(task):
                compacted += 1

    # 4. Save compacted plan
    if not _is_dry_run(args):
        save_plan(args.file, plan)

    if not getattr(args, "quiet", False):
        print(f"{_prefix(args)} Backed up to {backup_path}")
        print(f"{_prefix(args)} Compacted {compacted} completed task{'s' if compacted != 1 else ''}")
