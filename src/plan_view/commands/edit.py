"""Edit commands for modifying plan data."""

import argparse
import contextlib
import sys

from plan_view.formatting import VALID_STATUSES, now_iso
from plan_view.io import load_plan, save_plan
from plan_view.state import (
    find_phase,
    find_task,
    format_phase_suggestions,
    format_task_suggestions,
)


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
            "total_phases": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "overall_progress": 0,
        },
        "phases": [],
    }

    save_plan(path, plan)
    if not getattr(args, "quiet", False):
        print(f"✅ Created {path} for '{args.name}'")


def cmd_add_phase(args: argparse.Namespace) -> None:
    """Add a new phase."""
    path = args.file
    plan = load_plan(path)
    if plan is None:
        sys.exit(1)
    assert plan is not None

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
    save_plan(path, plan)
    if not getattr(args, "quiet", False):
        print(f"✅ Added Phase {next_id}: {args.name}")


def cmd_add_task(args: argparse.Namespace) -> None:
    """Add a new task to a phase."""
    path = args.file
    plan = load_plan(path)
    if plan is None:
        sys.exit(1)
    assert plan is not None

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
    save_plan(path, plan)
    if not getattr(args, "quiet", False):
        print(f"✅ Added [{next_id}] {args.title}")


def cmd_set(args: argparse.Namespace) -> None:
    """Set a task field."""
    path = args.file
    plan = load_plan(path)
    if plan is None:
        sys.exit(1)
    assert plan is not None

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

    save_plan(path, plan)
    if not getattr(args, "quiet", False):
        print(f"✅ [{args.id}] {args.field} → {args.value}")


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


def cmd_defer(args: argparse.Namespace) -> None:
    """Move task to deferred phase."""
    path = args.file
    plan = load_plan(path)
    if plan is None:
        sys.exit(1)
    assert plan is not None

    result = find_task(plan, args.id)
    if result is None:
        print(f"Error: Task '{args.id}' not found\n", file=sys.stderr)
        print(format_task_suggestions(plan), file=sys.stderr)
        sys.exit(1)
    assert result is not None

    old_phase, task = result

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

    # Remove from old phase
    old_phase["tasks"].remove(task)
    old_id = task["id"]

    # Generate new ID for deferred phase
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
    task["id"] = new_id

    # Add to deferred phase
    task_list = deferred["tasks"]
    assert isinstance(task_list, list)
    task_list.append(task)
    save_plan(path, plan)
    if not getattr(args, "quiet", False):
        print(f"✅ [{old_id}] → [{new_id}] (deferred)")


def cmd_rm(args: argparse.Namespace) -> None:
    """Remove a phase or task."""
    path = args.file
    plan = load_plan(path)
    if plan is None:
        sys.exit(1)
    assert plan is not None

    if args.type == "task":
        result = find_task(plan, args.id)
        if result is None:
            print(f"Error: Task '{args.id}' not found\n", file=sys.stderr)
            print(format_task_suggestions(plan), file=sys.stderr)
            sys.exit(1)
        assert result is not None
        phase, task = result
        phase["tasks"].remove(task)
        save_plan(path, plan)
        if not getattr(args, "quiet", False):
            print(f"✅ Removed task [{args.id}]")

    else:  # args.type == "phase" (argparse enforces this)
        phase = find_phase(plan, args.id)
        if phase is None:
            print(f"Error: Phase '{args.id}' not found\n", file=sys.stderr)
            print(format_phase_suggestions(plan), file=sys.stderr)
            sys.exit(1)
        assert phase is not None
        plan["phases"].remove(phase)
        save_plan(path, plan)
        if not getattr(args, "quiet", False):
            print(f"✅ Removed phase {args.id}")
