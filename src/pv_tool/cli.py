#!/usr/bin/env python3
"""CLI for pretty-printing plan.json files."""

from __future__ import annotations

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
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}


def c(text: str, *styles: str) -> str:
    """Apply ANSI color codes to text."""
    codes = "".join(COLORS.get(s, "") for s in styles)
    return f"{codes}{text}{COLORS['reset']}"


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
                # Check dependencies
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


def cmd_help() -> None:
    """Show help message."""
    print(
        """pv - Pretty print plan.json

Usage: pv [command] [file]

Commands:
  (none)     Full plan overview
  next       Next pending/in-progress task
  phase      Current phase with all tasks + deps
  current    Completed summary + current phase + next
  validate   Validate against schema
  help       Show this help

Examples:
  pv                  # Show full plan
  pv next             # What should I work on?
  pv current          # Where am I?
  pv validate         # Check plan.json is valid
  pv phase other.json # Custom file"""
    )


def cmd_next(plan: dict) -> None:
    """Show the next task to work on."""
    result = get_next_task(plan)
    if not result:
        print("No pending tasks found!")
        return

    phase, task = result
    icon = get_status_icon(task["status"])
    agent = task.get("agent_type") or "general-purpose"

    print(f"\n{c('Next Task:', 'bold')}")
    print(f"  {icon} [{task['id']}] {task['title']}")
    print(f"  {c('Phase:', 'dim')} {phase['name']}")
    print(f"  {c('Agent:', 'dim')} {agent}")

    deps = task.get("depends_on", [])
    if deps:
        print(f"  {c('Depends on:', 'dim')} {', '.join(deps)}")
    print()


def cmd_phase(plan: dict) -> None:
    """Show current phase with all tasks."""
    phase = get_current_phase(plan)
    if not phase:
        print("No active phase found!")
        return

    progress = phase.get("progress", {})
    pct = progress.get("percentage", 0)

    print(f"\n{c(f'Phase {phase[\"id\"]}: {phase[\"name\"]}', 'bold', 'cyan')}")
    print(f"   {phase['description']}")
    print(f"   Progress: {pct:.0f}% ({progress.get('completed', 0)}/{progress.get('total', 0)} tasks)\n")

    for task in phase.get("tasks", []):
        icon = get_status_icon(task["status"])
        agent = f"({task.get('agent_type') or 'general'})" if task.get("agent_type") else ""
        deps = task.get("depends_on", [])
        dep_str = f" [deps: {', '.join(deps)}]" if deps else ""

        print(f"   {icon} [{task['id']}] {task['title']} {c(agent, 'dim')}{c(dep_str, 'dim')}")
    print()


def cmd_current(plan: dict) -> None:
    """Show completed summary + current phase + next task."""
    meta = plan.get("meta", {})
    summary = plan.get("summary", {})

    # Header
    project = meta.get("project", "Unknown Project")
    version = meta.get("version", "0.0.0")
    total = summary.get("total_tasks", 0)
    completed = summary.get("completed_tasks", 0)
    pct = summary.get("overall_progress", 0)

    print(f"\n{c(f'📋 {project} v{version}', 'bold')}")
    print(f"Progress: {pct:.0f}% ({completed}/{total} tasks)\n")

    # Completed phases
    for phase in plan.get("phases", []):
        if phase["status"] == "completed":
            print(f"{c(f'✅ Phase {phase[\"id\"]}: {phase[\"name\"]} (100%)', 'green')}")

    # Current phase
    current = get_current_phase(plan)
    if current:
        progress = current.get("progress", {})
        pct = progress.get("percentage", 0)
        status_icon = "🔄" if current["status"] == "in_progress" else "⏳"

        print(f"\n{status_icon} {c(f'Phase {current[\"id\"]}: {current[\"name\"]} ({pct:.0f}%)', 'bold', 'yellow')}")
        print(f"   {current['description']}\n")

        for task in current.get("tasks", []):
            icon = get_status_icon(task["status"])
            agent = task.get("agent_type") or "general"
            print(f"   {icon} [{task['id']}] {task['title']} {c(f'({agent})', 'dim')}")

    # Next task
    result = get_next_task(plan)
    if result:
        _, task = result
        print(f"\n{c('👉 Next:', 'bold')} [{task['id']}] {task['title']}")
    print()


def cmd_validate(plan: dict, path: Path) -> None:
    """Validate plan against schema."""
    # Basic structural validation (full jsonschema validation would require dependency)
    errors = []

    if "meta" not in plan:
        errors.append("Missing 'meta' section")
    if "summary" not in plan:
        errors.append("Missing 'summary' section")
    if "phases" not in plan:
        errors.append("Missing 'phases' section")

    for i, phase in enumerate(plan.get("phases", [])):
        if "id" not in phase:
            errors.append(f"Phase {i}: missing 'id'")
        if "tasks" not in phase:
            errors.append(f"Phase {phase.get('id', i)}: missing 'tasks'")

        for j, task in enumerate(phase.get("tasks", [])):
            if "id" not in task:
                errors.append(f"Phase {phase.get('id', i)}, Task {j}: missing 'id'")
            if "status" not in task:
                errors.append(f"Task {task.get('id', j)}: missing 'status'")

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

    print(f"\n{c(f'📋 {project} v{version}', 'bold')}")
    print(f"Progress: {summary.get('overall_progress', 0):.0f}% ({summary.get('completed_tasks', 0)}/{summary.get('total_tasks', 0)} tasks)\n")

    for phase in plan.get("phases", []):
        progress = phase.get("progress", {})
        pct = progress.get("percentage", 0)
        icon = get_status_icon(phase["status"])

        print(f"{icon} {c(f'Phase {phase[\"id\"]}: {phase[\"name\"]}', 'bold')} ({pct:.0f}%)")
        print(f"   {phase['description']}\n")

        for task in phase.get("tasks", []):
            t_icon = get_status_icon(task["status"])
            agent = task.get("agent_type") or "general"
            print(f"   {t_icon} [{task['id']}] {task['title']} {c(f'({agent})', 'dim')}")
        print()


def main() -> None:
    """Main entry point."""
    args = sys.argv[1:]

    # Parse command and file
    command = ""
    file_path = Path("plan.json")

    for arg in args:
        if arg in ("help", "-h", "--help"):
            cmd_help()
            return
        elif arg in ("next", "phase", "current", "validate"):
            command = arg
        elif arg.endswith(".json"):
            file_path = Path(arg)

    # Load plan
    plan = load_plan(file_path)
    if not plan:
        sys.exit(1)

    # Execute command
    if command == "next":
        cmd_next(plan)
    elif command == "phase":
        cmd_phase(plan)
    elif command == "current":
        cmd_current(plan)
    elif command == "validate":
        cmd_validate(plan, file_path)
    else:
        cmd_overview(plan)


if __name__ == "__main__":
    main()
