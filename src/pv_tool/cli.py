#!/usr/bin/env python3
"""CLI for pretty-printing plan.json files."""

import argparse
import json
import sys
from pathlib import Path

# Status icons
ICONS = {
    "completed": "✅",
    "in_progress": "🔄",
    "pending": "⏳",
    "blocked": "🛑",
    "skipped": "⏭️",
}

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


def yellow(text: str) -> str:
    return f"{YELLOW}{text}{RESET}"


def cyan(text: str) -> str:
    return f"{CYAN}{text}{RESET}"


def bold_cyan(text: str) -> str:
    return f"{BOLD}{CYAN}{text}{RESET}"


def bold_yellow(text: str) -> str:
    return f"{BOLD}{YELLOW}{text}{RESET}"


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


def get_status_icon(status: str) -> str:
    """Get emoji icon for status."""
    return ICONS.get(status, "❓")


def get_current_phase(plan: dict) -> dict | None:
    """Find the current (in_progress or first pending) phase."""
    for phase in plan.get("phases", []):
        if phase["status"] == "in_progress":
            return phase
    for phase in plan.get("phases", []):
        if phase["status"] == "pending":
            return phase
    return None


def get_next_task(plan: dict) -> tuple[dict, dict] | None:
    """Find the next pending or in_progress task."""
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


def cmd_next(plan: dict) -> None:
    """Show the next task to work on."""
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
    """Show current phase with all tasks."""
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


def cmd_current(plan: dict) -> None:
    """Show completed summary + current phase + next task."""
    meta = plan.get("meta", {})
    summary = plan.get("summary", {})

    project = meta.get("project", "Unknown Project")
    version = meta.get("version", "0.0.0")
    total = summary.get("total_tasks", 0)
    completed = summary.get("completed_tasks", 0)
    pct = summary.get("overall_progress", 0)

    print(f"\n{bold(f'📋 {project} v{version}')}")
    print(f"Progress: {pct:.0f}% ({completed}/{total} tasks)\n")

    # Completed phases
    for phase in plan.get("phases", []):
        if phase["status"] == "completed":
            phase_id = phase["id"]
            phase_name = phase["name"]
            print(green(f"✅ Phase {phase_id}: {phase_name} (100%)"))

    # Current phase
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

    # Next task
    result = get_next_task(plan)
    if result:
        _, task = result
        task_id = task["id"]
        task_title = task["title"]
        print(f"\n{bold('👉 Next:')} [{task_id}] {task_title}")
    print()


def cmd_validate(plan: dict, path: Path) -> None:
    """Validate plan against schema."""
    errors = []

    if "meta" not in plan:
        errors.append("Missing 'meta' section")
    if "summary" not in plan:
        errors.append("Missing 'summary' section")
    if "phases" not in plan:
        errors.append("Missing 'phases' section")

    for i, phase in enumerate(plan.get("phases", [])):
        phase_id = phase.get("id", str(i))
        if "id" not in phase:
            errors.append(f"Phase {i}: missing 'id'")
        if "tasks" not in phase:
            errors.append(f"Phase {phase_id}: missing 'tasks'")

        for j, task in enumerate(phase.get("tasks", [])):
            task_id = task.get("id", str(j))
            if "id" not in task:
                errors.append(f"Phase {phase_id}, Task {j}: missing 'id'")
            if "status" not in task:
                errors.append(f"Task {task_id}: missing 'status'")

    if errors:
        print(f"❌ Validation failed for {path}:")
        for err in errors:
            print(f"   - {err}")
        sys.exit(1)
    else:
        print(f"✅ {path} is valid")


def cmd_overview(plan: dict) -> None:
    """Show full plan overview."""
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


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="pv",
        description="Pretty print plan.json for task tracking",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["next", "phase", "current", "validate"],
        default=None,
        help="Command to run (default: full overview)",
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        default=Path("plan.json"),
        help="Path to plan.json (default: ./plan.json)",
    )

    args = parser.parse_args()

    plan = load_plan(args.file)
    if not plan:
        sys.exit(1)

    match args.command:
        case "next":
            cmd_next(plan)
        case "phase":
            cmd_phase(plan)
        case "current":
            cmd_current(plan)
        case "validate":
            cmd_validate(plan, args.file)
        case _:
            cmd_overview(plan)


if __name__ == "__main__":
    main()
