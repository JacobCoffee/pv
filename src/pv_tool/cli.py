#!/usr/bin/env python3
"""CLI for viewing and editing plan.json files."""

import argparse
import json
import sys
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path

import jsonschema

# Status icons
ICONS = {
    "completed": "✅",
    "in_progress": "🔄",
    "pending": "⏳",
    "blocked": "🛑",
    "skipped": "⏭️",
}

VALID_STATUSES = ("pending", "in_progress", "completed", "blocked", "skipped")

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def bold(text: str) -> str:
    return f"{BOLD}{text}{RESET}"


def dim(text: str) -> str:
    return f"{DIM}{text}{RESET}"


def green(text: str) -> str:
    return f"{GREEN}{text}{RESET}"


def bold_cyan(text: str) -> str:
    return f"{BOLD}{CYAN}{text}{RESET}"


def bold_yellow(text: str) -> str:
    return f"{BOLD}{YELLOW}{text}{RESET}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def recalculate_progress(plan: dict) -> None:
    """Recalculate all progress fields."""
    total_tasks = 0
    completed_tasks = 0

    for phase in plan.get("phases", []):
        tasks = phase.get("tasks", [])
        phase_total = len(tasks)
        phase_completed = sum(1 for t in tasks if t["status"] == "completed")

        phase["progress"] = {
            "completed": phase_completed,
            "total": phase_total,
            "percentage": (phase_completed / phase_total * 100) if phase_total > 0 else 0,
        }

        # Update phase status based on tasks
        if phase_completed == phase_total and phase_total > 0:
            phase["status"] = "completed"
        elif any(t["status"] == "in_progress" for t in tasks):
            phase["status"] = "in_progress"
        elif phase_completed > 0:
            phase["status"] = "in_progress"

        total_tasks += phase_total
        completed_tasks += phase_completed

    plan["summary"] = {
        "total_phases": len(plan.get("phases", [])),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overall_progress": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
    }


def get_status_icon(status: str) -> str:
    return ICONS.get(status, "❓")


def get_current_phase(plan: dict) -> dict | None:
    for phase in plan.get("phases", []):
        if phase["status"] == "in_progress":
            return phase
    for phase in plan.get("phases", []):
        if phase["status"] == "pending":
            return phase
    return None


def get_next_task(plan: dict) -> tuple[dict, dict] | None:
    for phase in plan.get("phases", []):
        if phase["status"] in ("completed", "skipped"):
            continue
        for task in phase.get("tasks", []):
            if task["status"] == "in_progress":
                return phase, task
            if task["status"] == "pending":
                deps = task.get("depends_on", [])
                all_deps_met = True
                for dep in deps:
                    for p in plan.get("phases", []):
                        for t in p.get("tasks", []):
                            if t["id"] == dep and t["status"] != "completed":
                                all_deps_met = False
                                break
                if all_deps_met:
                    return phase, task
    return None


def find_task(plan: dict, task_id: str) -> tuple[dict, dict] | None:
    """Find a task by ID, return (phase, task) or None."""
    for phase in plan.get("phases", []):
        for task in phase.get("tasks", []):
            if task["id"] == task_id:
                return phase, task
    return None


def find_phase(plan: dict, phase_id: str) -> dict | None:
    """Find a phase by ID."""
    for phase in plan.get("phases", []):
        if phase["id"] == phase_id:
            return phase
    return None


# ============ VIEW COMMANDS ============


def cmd_overview(plan: dict) -> None:
    meta = plan.get("meta", {})
    summary = plan.get("summary", {})

    project = meta.get("project", "Unknown Project")
    version = meta.get("version", "0.0.0")
    total = summary.get("total_tasks", 0)
    completed = summary.get("completed_tasks", 0)
    pct = summary.get("overall_progress", 0)

    print(f"\n{bold(f'📋 {project} v{version}')}")
    print(f"Progress: {pct:.0f}% ({completed}/{total} tasks)\n")

    for phase in plan.get("phases", []):
        progress = phase.get("progress", {})
        phase_pct = progress.get("percentage", 0)
        icon = get_status_icon(phase["status"])
        phase_id = phase["id"]
        phase_name = phase["name"]
        phase_desc = phase["description"]

        print(f"{icon} {bold(f'Phase {phase_id}: {phase_name}')} ({phase_pct:.0f}%)")
        print(f"   {phase_desc}\n")

        for task in phase.get("tasks", []):
            t_icon = get_status_icon(task["status"])
            task_id = task["id"]
            task_title = task["title"]
            agent = task.get("agent_type") or "general"
            print(f"   {t_icon} [{task_id}] {task_title} {dim(f'({agent})')}")
        print()


def cmd_current(plan: dict) -> None:
    meta = plan.get("meta", {})
    summary = plan.get("summary", {})

    project = meta.get("project", "Unknown Project")
    version = meta.get("version", "0.0.0")
    total = summary.get("total_tasks", 0)
    completed = summary.get("completed_tasks", 0)
    pct = summary.get("overall_progress", 0)

    print(f"\n{bold(f'📋 {project} v{version}')}")
    print(f"Progress: {pct:.0f}% ({completed}/{total} tasks)\n")

    for phase in plan.get("phases", []):
        if phase["status"] == "completed":
            phase_id = phase["id"]
            phase_name = phase["name"]
            print(green(f"✅ Phase {phase_id}: {phase_name} (100%)"))

    current = get_current_phase(plan)
    if current:
        progress = current.get("progress", {})
        pct = progress.get("percentage", 0)
        status_icon = "🔄" if current["status"] == "in_progress" else "⏳"
        phase_id = current["id"]
        phase_name = current["name"]
        phase_desc = current["description"]

        print(f"\n{status_icon} {bold_yellow(f'Phase {phase_id}: {phase_name} ({pct:.0f}%)')}")
        print(f"   {phase_desc}\n")

        for task in current.get("tasks", []):
            icon = get_status_icon(task["status"])
            task_id = task["id"]
            task_title = task["title"]
            agent = task.get("agent_type") or "general"
            print(f"   {icon} [{task_id}] {task_title} {dim(f'({agent})')}")

    result = get_next_task(plan)
    if result:
        _, task = result
        task_id = task["id"]
        task_title = task["title"]
        print(f"\n{bold('👉 Next:')} [{task_id}] {task_title}")
    print()


def cmd_next(plan: dict) -> None:
    result = get_next_task(plan)
    if not result:
        print("No pending tasks found!")
        return

    phase, task = result
    icon = get_status_icon(task["status"])
    agent = task.get("agent_type") or "general-purpose"
    task_id = task["id"]
    task_title = task["title"]
    phase_name = phase["name"]

    print(f"\n{bold('Next Task:')}")
    print(f"  {icon} [{task_id}] {task_title}")
    print(f"  {dim('Phase:')} {phase_name}")
    print(f"  {dim('Agent:')} {agent}")

    deps = task.get("depends_on", [])
    if deps:
        deps_str = ", ".join(deps)
        print(f"  {dim('Depends on:')} {deps_str}")
    print()


def cmd_phase(plan: dict) -> None:
    phase = get_current_phase(plan)
    if not phase:
        print("No active phase found!")
        return

    progress = phase.get("progress", {})
    pct = progress.get("percentage", 0)
    phase_id = phase["id"]
    phase_name = phase["name"]
    phase_desc = phase["description"]
    completed = progress.get("completed", 0)
    total = progress.get("total", 0)

    print(f"\n{bold_cyan(f'Phase {phase_id}: {phase_name}')}")
    print(f"   {phase_desc}")
    print(f"   Progress: {pct:.0f}% ({completed}/{total} tasks)\n")

    for task in phase.get("tasks", []):
        icon = get_status_icon(task["status"])
        task_id = task["id"]
        task_title = task["title"]
        agent = task.get("agent_type") or "general"
        agent_str = f"({agent})" if task.get("agent_type") else ""
        deps = task.get("depends_on", [])
        dep_str = f" [deps: {', '.join(deps)}]" if deps else ""

        print(f"   {icon} [{task_id}] {task_title} {dim(agent_str)}{dim(dep_str)}")
    print()


def load_schema() -> dict:
    """Load the bundled JSON schema."""
    schema_path = files("pv_tool").joinpath("plan.schema.json")
    return json.loads(schema_path.read_text())


def cmd_validate(plan: dict, path: Path) -> None:
    """Validate plan against JSON schema."""
    schema = load_schema()

    try:
        jsonschema.validate(plan, schema)
        print(f"✅ {path} is valid")
    except jsonschema.ValidationError as e:
        print(f"❌ Validation failed for {path}:")
        print(f"   {e.message}")
        if e.absolute_path:
            json_path = ".".join(str(p) for p in e.absolute_path)
            print(f"   Path: {json_path}")
        sys.exit(1)


# ============ EDIT COMMANDS ============


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
    print(f"✅ Created {path} for '{args.name}'")


def cmd_add_phase(args: argparse.Namespace) -> None:
    """Add a new phase."""
    path = args.file
    plan = load_plan(path)
    if not plan:
        sys.exit(1)

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
    print(f"✅ Added Phase {next_id}: {args.name}")


def cmd_add_task(args: argparse.Namespace) -> None:
    """Add a new task to a phase."""
    path = args.file
    plan = load_plan(path)
    if not plan:
        sys.exit(1)

    phase = find_phase(plan, args.phase)
    if not phase:
        print(f"Error: Phase '{args.phase}' not found", file=sys.stderr)
        sys.exit(1)

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
    if not existing_tasks:
        next_id = f"{phase_id}.1.1"
    else:
        next_id = f"{phase_id}.{max_section}.{max_task + 1}"

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
    print(f"✅ Added [{next_id}] {args.title}")


def cmd_set(args: argparse.Namespace) -> None:
    """Set a task field."""
    path = args.file
    plan = load_plan(path)
    if not plan:
        sys.exit(1)

    result = find_task(plan, args.id)
    if not result:
        print(f"Error: Task '{args.id}' not found", file=sys.stderr)
        sys.exit(1)

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


def cmd_rm(args: argparse.Namespace) -> None:
    """Remove a phase or task."""
    path = args.file
    plan = load_plan(path)
    if not plan:
        sys.exit(1)

    if args.type == "task":
        result = find_task(plan, args.id)
        if not result:
            print(f"Error: Task '{args.id}' not found", file=sys.stderr)
            sys.exit(1)
        phase, task = result
        phase["tasks"].remove(task)
        save_plan(path, plan)
        print(f"✅ Removed task [{args.id}]")

    elif args.type == "phase":
        phase = find_phase(plan, args.id)
        if not phase:
            print(f"Error: Phase '{args.id}' not found", file=sys.stderr)
            sys.exit(1)
        plan["phases"].remove(phase)
        save_plan(path, plan)
        print(f"✅ Removed phase {args.id}")


# ============ MAIN ============


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pv",
        description="View and edit plan.json for task tracking",
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        default=Path("plan.json"),
        help="Path to plan.json (default: ./plan.json)",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # View commands (also work without subcommand)
    subparsers.add_parser("current", help="Show current progress and next task")
    subparsers.add_parser("next", help="Show next task to work on")
    subparsers.add_parser("phase", help="Show current phase details")
    subparsers.add_parser("validate", help="Validate plan.json structure")

    # Init
    init_p = subparsers.add_parser("init", help="Create new plan.json")
    init_p.add_argument("name", help="Project name")
    init_p.add_argument("--force", action="store_true", help="Overwrite existing file")

    # Add phase
    add_phase_p = subparsers.add_parser("add-phase", help="Add a new phase")
    add_phase_p.add_argument("name", help="Phase name")
    add_phase_p.add_argument("--desc", help="Phase description")

    # Add task
    add_task_p = subparsers.add_parser("add-task", help="Add a new task")
    add_task_p.add_argument("phase", help="Phase ID to add task to")
    add_task_p.add_argument("title", help="Task title")
    add_task_p.add_argument("--agent", help="Agent type")
    add_task_p.add_argument("--deps", help="Comma-separated dependency task IDs")

    # Set field
    set_p = subparsers.add_parser("set", help="Set a task field")
    set_p.add_argument("id", help="Task ID")
    set_p.add_argument("field", help="Field to set (status, agent, title)")
    set_p.add_argument("value", help="New value")

    # Shortcuts
    done_p = subparsers.add_parser("done", help="Mark task as completed")
    done_p.add_argument("id", help="Task ID")

    start_p = subparsers.add_parser("start", help="Mark task as in_progress")
    start_p.add_argument("id", help="Task ID")

    # Remove
    rm_p = subparsers.add_parser("rm", help="Remove a phase or task")
    rm_p.add_argument("type", choices=["phase", "task"], help="What to remove")
    rm_p.add_argument("id", help="ID to remove")

    args = parser.parse_args()

    # Handle edit commands that don't need to load plan first
    match args.command:
        case "init":
            cmd_init(args)
            return
        case "add-phase":
            cmd_add_phase(args)
            return
        case "add-task":
            cmd_add_task(args)
            return
        case "set":
            cmd_set(args)
            return
        case "done":
            cmd_done(args)
            return
        case "start":
            cmd_start(args)
            return
        case "rm":
            cmd_rm(args)
            return

    # View commands need to load plan
    plan = load_plan(args.file)
    if not plan:
        sys.exit(1)

    match args.command:
        case "current":
            cmd_current(plan)
        case "next":
            cmd_next(plan)
        case "phase":
            cmd_phase(plan)
        case "validate":
            cmd_validate(plan, args.file)
        case _:
            cmd_overview(plan)


if __name__ == "__main__":
    main()
