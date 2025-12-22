"""Plan state calculations and lookup operations."""

# Special phases that are not part of regular workflow
SPECIAL_PHASE_IDS = {"deferred", "99", "ideas"}


def _is_special_phase(phase: dict) -> bool:
    """Check if phase is a special holding phase (deferred/bugs)."""
    return phase["id"] in SPECIAL_PHASE_IDS


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
        elif any(t["status"] == "in_progress" for t in tasks) or phase_completed > 0:
            phase["status"] = "in_progress"

        total_tasks += phase_total
        completed_tasks += phase_completed

    plan["summary"] = {
        "total_phases": len(plan.get("phases", [])),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overall_progress": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
    }


def get_current_phase(plan: dict) -> dict | None:
    """Find the current in_progress or first pending phase (skips special phases)."""
    for phase in plan.get("phases", []):
        if _is_special_phase(phase):
            continue
        if phase["status"] == "in_progress":
            return phase
    for phase in plan.get("phases", []):
        if _is_special_phase(phase):
            continue
        if phase["status"] == "pending":
            return phase
    return None


def get_next_task(plan: dict) -> tuple[dict, dict] | None:
    """Find the next actionable task with all dependencies met (skips special phases)."""
    # Build task status lookup for O(1) dependency checks
    task_status = {t["id"]: t["status"] for p in plan.get("phases", []) for t in p.get("tasks", [])}

    for phase in plan.get("phases", []):
        if _is_special_phase(phase):
            continue
        if phase["status"] in ("completed", "skipped"):
            continue
        for task in phase.get("tasks", []):
            if task["status"] == "in_progress":
                return phase, task
            if task["status"] == "pending":
                deps = task.get("depends_on", [])
                if all(task_status.get(dep) == "completed" for dep in deps):
                    return phase, task
    return None


def find_task(plan: dict, task_id: str) -> tuple[dict, dict] | None:
    """Find a task by ID (exact or prefix match), return (phase, task) or None."""
    # Try exact match first
    for phase in plan.get("phases", []):
        for task in phase.get("tasks", []):
            if task["id"] == task_id:
                return phase, task

    # Try prefix match - return if exactly one match
    matches = [
        (phase, task)
        for phase in plan.get("phases", [])
        for task in phase.get("tasks", [])
        if task["id"].startswith(task_id)
    ]
    return matches[0] if len(matches) == 1 else None


def find_phase(plan: dict, phase_id: str) -> dict | None:
    """Find a phase by ID."""
    for phase in plan.get("phases", []):
        if phase["id"] == phase_id:
            return phase
    return None


def task_to_dict(phase: dict, task: dict) -> dict:
    """Convert a task to a JSON-serializable dict."""
    return {
        "id": task["id"],
        "title": task["title"],
        "status": task["status"],
        "phase_id": phase["id"],
        "phase_name": phase["name"],
        "agent_type": task.get("agent_type"),
        "depends_on": task.get("depends_on", []),
        "tracking": task.get("tracking", {}),
    }


def get_all_task_ids(plan: dict, limit: int = 5) -> list[tuple[str, str, str]]:
    """Get task IDs with titles and phase names (limited for display)."""
    tasks = []
    for phase in plan.get("phases", []):
        for task in phase.get("tasks", []):
            tasks.append((task["id"], task["title"], phase["name"]))
            if len(tasks) >= limit:
                return tasks
    return tasks


def get_all_phase_ids(plan: dict) -> list[tuple[str, str]]:
    """Get phase IDs with names."""
    return [(p["id"], p["name"]) for p in plan.get("phases", [])]


def format_task_suggestions(plan: dict, limit: int = 5) -> str:
    """Format task suggestions for error messages."""
    tasks = get_all_task_ids(plan, limit)
    if not tasks:
        return "No tasks found. Use 'pv add-task' to create one."
    lines = ["Available tasks:"]
    for task_id, title, _phase_name in tasks:
        # Truncate long titles
        display_title = title[:30] + "..." if len(title) > 30 else title
        lines.append(f"  {task_id}  {display_title}")
    total = sum(len(p.get("tasks", [])) for p in plan.get("phases", []))
    if total > limit:
        lines.append(f"  ... and {total - limit} more (use 'pv' to see all)")
    return "\n".join(lines)


def format_phase_suggestions(plan: dict) -> str:
    """Format phase suggestions for error messages."""
    phases = get_all_phase_ids(plan)
    if not phases:
        return "No phases found. Use 'pv add-phase' to create one."
    lines = ["Available phases:"]
    for phase_id, name in phases:
        lines.append(f"  {phase_id}  {name}")
    return "\n".join(lines)
