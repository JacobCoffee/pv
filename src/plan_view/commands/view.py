"""View commands for displaying plan information."""

import json
import sys
from pathlib import Path

import jsonschema

from plan_view.formatting import ICONS, bold, bold_cyan, bold_yellow, dim, green
from plan_view.io import load_schema
from plan_view.state import find_phase, find_task, get_current_phase, get_next_task, task_to_dict

HELP_TEXT = """\
View and edit plan.json for task tracking

View Commands:
  (none)              Show full plan overview
  current, c          Show current progress and next task
  next, n             Show next task to work on
  phase, p            Show current phase details
  get, g ID           Show a specific task or phase by ID
  last, l [-a]        Show recently completed tasks (-a for all)
  summary, s          Show plan summary (pretty output, use --json for JSON)
  bugs, b             Show bugs phase with all tasks
  deferred, d         Show deferred phase with all tasks
  validate, v         Validate plan.json structure

Edit Commands:
  init NAME           Create new plan.json
  add-phase NAME      Add a new phase
  add-task PHASE TITLE  Add a new task to a phase
  set ID FIELD VALUE  Set a task field (status, agent, title)
  done ID             Mark task as completed
  start ID            Mark task as in_progress
  block ID            Mark task as blocked
  skip ID             Mark task as skipped
  defer ID|TITLE      Move task to deferred, or add new deferred task
  bug ID|TITLE        Move task to bugs, or add new bug task
  rm TYPE ID          Remove a phase or task

Options:
  -f, --file FILE     Path to plan.json (default: ./plan.json)
  --json              Output as JSON (view commands only)
  -q, --quiet         Suppress output (edit commands only)
  -d, --dry-run       Show what would change without saving
  -h, --help          Show this help message
"""


def cmd_overview(plan: dict, *, as_json: bool = False) -> None:
    """Display full plan overview with all phases and tasks."""
    if as_json:
        print(json.dumps(plan, indent=2))
        return

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
        icon = ICONS.get(phase["status"], "❓")
        phase_id = phase["id"]
        phase_name = phase["name"]
        phase_desc = phase["description"]

        print(f"{icon} {bold(f'Phase {phase_id}: {phase_name}')} ({phase_pct:.0f}%)")
        print(f"   {phase_desc}\n")

        for task in phase.get("tasks", []):
            t_icon = ICONS.get(task["status"], "❓")
            task_id = task["id"]
            task_title = task["title"]
            agent = task.get("agent_type") or "general"
            print(f"   {t_icon} [{task_id}] {task_title} {dim(f'({agent})')}")
        print()


def cmd_current(plan: dict, *, as_json: bool = False) -> None:
    """Display completed phases summary, current phase, and next task."""
    if as_json:
        current = get_current_phase(plan)
        result = get_next_task(plan)
        output = {
            "summary": plan.get("summary", {}),
            "current_phase": current,
            "next_task": task_to_dict(*result) if result else None,
        }
        print(json.dumps(output, indent=2))
        return

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
            icon = ICONS.get(task["status"], "❓")
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


def cmd_next(plan: dict, *, as_json: bool = False) -> None:
    """Display the next task to work on."""
    result = get_next_task(plan)
    if not result:
        if as_json:
            print("null")
        else:
            print("No pending tasks found!")
        return

    phase, task = result

    if as_json:
        print(json.dumps(task_to_dict(phase, task), indent=2))
        return

    icon = ICONS.get(task["status"], "❓")
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


def cmd_phase(plan: dict, *, as_json: bool = False) -> None:
    """Display current phase details with all tasks and dependencies."""
    phase = get_current_phase(plan)
    if not phase:
        if as_json:
            print("null")
        else:
            print("No active phase found!")
        return

    if as_json:
        print(json.dumps(phase, indent=2))
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
        icon = ICONS.get(task["status"], "❓")
        task_id = task["id"]
        task_title = task["title"]
        agent = task.get("agent_type") or "general"
        agent_str = f"({agent})" if task.get("agent_type") else ""
        deps = task.get("depends_on", [])
        dep_str = f" [deps: {', '.join(deps)}]" if deps else ""

        print(f"   {icon} [{task_id}] {task_title} {dim(agent_str)}{dim(dep_str)}")
    print()


def cmd_get(plan: dict, task_id: str, *, as_json: bool = False) -> None:
    """Display a specific task or phase by ID."""
    # Try to find as a task first
    result = find_task(plan, task_id)
    if result:
        phase, task = result

        if as_json:
            print(json.dumps(task_to_dict(phase, task), indent=2))
            return

        icon = ICONS.get(task["status"], "❓")
        agent = task.get("agent_type") or "general-purpose"
        tracking = task.get("tracking", {})

        print(f"\n{bold(f'[{task_id}] {task["title"]}')}")
        print(f"  {dim('Status:')} {icon} {task['status']}")
        print(f"  {dim('Phase:')} {phase['name']}")
        print(f"  {dim('Agent:')} {agent}")

        deps = task.get("depends_on", [])
        if deps:
            print(f"  {dim('Depends on:')} {', '.join(deps)}")

        if tracking.get("started_at"):
            print(f"  {dim('Started:')} {tracking['started_at'][:10]}")
        if tracking.get("completed_at"):
            print(f"  {dim('Completed:')} {tracking['completed_at'][:10]}")
        print()
        return

    # If not a task, try to find as a phase
    phase = find_phase(plan, task_id)
    if phase:
        if as_json:
            print(json.dumps(phase, indent=2))
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
            icon = ICONS.get(task["status"], "❓")
            task_id_display = task["id"]
            task_title = task["title"]
            agent = task.get("agent_type") or "general"
            agent_str = f"({agent})" if task.get("agent_type") else ""
            deps = task.get("depends_on", [])
            dep_str = f" [deps: {', '.join(deps)}]" if deps else ""

            print(f"   {icon} [{task_id_display}] {task_title} {dim(agent_str)}{dim(dep_str)}")
        print()
        return

    # Not found as either task or phase
    if as_json:
        print("null")
    else:
        print(f"Task or phase '{task_id}' not found!")
    return


def cmd_last(plan: dict, count: int | None = 5, *, as_json: bool = False) -> None:
    """Display recently completed tasks."""
    completed_tasks = []

    for phase in plan.get("phases", []):
        for task in phase.get("tasks", []):
            if task["status"] == "completed":
                tracking = task.get("tracking", {})
                completed_at = tracking.get("completed_at")
                completed_tasks.append((phase, task, completed_at))

    if not completed_tasks:
        if as_json:
            print("[]")
        else:
            print("No completed tasks found!")
        return

    # Sort by completion time (most recent first), tasks without timestamp go last
    completed_tasks.sort(key=lambda x: x[2] or "", reverse=True)

    if as_json:
        output = [
            {
                "id": task["id"],
                "title": task["title"],
                "phase_id": phase["id"],
                "phase_name": phase["name"],
                "completed_at": completed_at,
                "agent_type": task.get("agent_type"),
            }
            for phase, task, completed_at in completed_tasks[:count]
        ]
        print(json.dumps(output, indent=2))
        return

    print(f"\n{bold('Recently Completed:')}\n")
    for phase, task, completed_at in completed_tasks[:count]:
        task_id = task["id"]
        task_title = task["title"]
        phase_name = phase["name"]
        time_str = completed_at[:10] if completed_at else "unknown"
        print(f"   ✅ [{task_id}] {task_title}")
        print(f"      {dim(f'{phase_name} · {time_str}')}")
    print()


def cmd_summary(plan: dict, *, as_json: bool = False) -> None:
    """Display summary of plan progress."""
    meta = plan.get("meta", {})
    summary = plan.get("summary", {})

    if as_json:
        output = {
            "project": meta.get("project"),
            "version": meta.get("version"),
            **summary,
        }
        print(json.dumps(output))
        return

    # Pretty output (default)
    project = meta.get("project", "Unknown Project")
    version = meta.get("version", "0.0.0")
    total = summary.get("total_tasks", 0)
    completed = summary.get("completed_tasks", 0)
    pct = summary.get("overall_progress", 0)

    print(f"\n{bold(f'📋 {project} v{version}')}")
    print(f"Overall Progress: {pct:.1f}% ({completed}/{total} tasks)\n")

    # Phase-by-phase breakdown
    print(bold("Phase Breakdown:"))
    for phase in plan.get("phases", []):
        progress = phase.get("progress", {})
        phase_pct = progress.get("percentage", 0)
        phase_completed = progress.get("completed", 0)
        phase_total = progress.get("total", 0)
        icon = ICONS.get(phase["status"], "❓")
        phase_id = phase["id"]
        phase_name = phase["name"]

        print(f"  {icon} Phase {phase_id}: {phase_name}")
        print(f"     {phase_pct:.1f}% ({phase_completed}/{phase_total} tasks)")
    print()


def cmd_validate(plan: dict, path: Path, *, as_json: bool = False) -> None:
    """Validate plan against JSON schema."""
    schema = load_schema()

    try:
        jsonschema.validate(plan, schema)
        if as_json:
            print(json.dumps({"valid": True, "path": str(path)}))
        else:
            print(f"✅ {path} is valid")
    except jsonschema.ValidationError as e:
        if as_json:
            json_path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else None
            print(json.dumps({"valid": False, "path": str(path), "error": e.message, "json_path": json_path}))
        else:
            print(f"❌ Validation failed for {path}:")
            print(f"   {e.message}")
            if e.absolute_path:
                json_path = ".".join(str(p) for p in e.absolute_path)
                print(f"   Path: {json_path}")
        sys.exit(1)


def _display_special_phase(plan: dict, phase_id: str, phase_name: str, *, as_json: bool = False) -> None:
    """Display a special phase (bugs or deferred)."""
    phase = find_phase(plan, phase_id)
    if phase is None:
        if as_json:
            print("null")
        else:
            print(f"No {phase_name.lower()} phase found!")
        return

    if as_json:
        print(json.dumps(phase, indent=2))
        return

    tasks = phase.get("tasks", [])
    progress = phase.get("progress", {})
    completed = progress.get("completed", 0)
    total = progress.get("total", 0)

    print(f"\n{bold_cyan(f'{phase_name} ({total} tasks)')}")
    print(f"   {phase['description']}")
    if total > 0:
        print(f"   Completed: {completed}/{total}\n")
    else:
        print()

    if not tasks:
        print(f"   No {phase_name.lower()} tasks.\n")
        return

    for task in tasks:
        icon = ICONS.get(task["status"], "❓")
        task_id = task["id"]
        task_title = task["title"]
        agent = task.get("agent_type") or "general"
        agent_str = f"({agent})" if task.get("agent_type") else ""
        print(f"   {icon} [{task_id}] {task_title} {dim(agent_str)}")
    print()


def cmd_bugs(plan: dict, *, as_json: bool = False) -> None:
    """Display bugs phase with all tasks."""
    _display_special_phase(plan, "99", "Bugs", as_json=as_json)


def cmd_deferred(plan: dict, *, as_json: bool = False) -> None:
    """Display deferred phase with all tasks."""
    _display_special_phase(plan, "deferred", "Deferred", as_json=as_json)
