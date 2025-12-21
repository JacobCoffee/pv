"""Builder pattern classes for test data construction.

Provides fluent interfaces for building Task, Phase, and Plan test fixtures with sensible defaults.

Example usage:
    # Simple task
    task = TaskBuilder().with_id("1.1.1").with_title("My Task").build()

    # Completed task with tracking
    task = (TaskBuilder()
            .with_id("1.1.1")
            .with_title("Done Task")
            .with_status("completed")
            .completed_at("2025-01-01T00:00:00Z")
            .build())

    # Task with dependencies
    task = (TaskBuilder()
            .with_id("1.1.2")
            .depends_on(["1.1.1"])
            .with_agent("python-backend-engineer")
            .build())

    # Phase with multiple tasks
    phase = (PhaseBuilder()
             .with_id("1")
             .with_name("Development")
             .add_task(TaskBuilder().with_id("1.1.1").build())
             .add_task(TaskBuilder().with_id("1.1.2").build())
             .build())

    # Complete plan
    plan = (PlanBuilder()
            .with_project("Test Project")
            .add_phase(PhaseBuilder().with_id("0").build())
            .build())
"""

from typing import Any


class TaskBuilder:
    """Builder for Task test data with fluent interface.

    Provides sensible defaults for all required fields and allows
    customization through method chaining.
    """

    def __init__(self):
        """Initialize with default task values."""
        self._data: dict[str, Any] = {
            "id": "0.1.1",
            "title": "Test Task",
            "status": "pending",
            "agent_type": None,
            "depends_on": [],
            "tracking": {},
        }

    def with_id(self, task_id: str) -> TaskBuilder:
        """Set the task ID (format: X.Y.Z)."""
        self._data["id"] = task_id
        return self

    def with_title(self, title: str) -> TaskBuilder:
        """Set the task title."""
        self._data["title"] = title
        return self

    def with_status(self, status: str) -> TaskBuilder:
        """Set the task status.

        Args:
            status: One of: pending, in_progress, completed, blocked, skipped
        """
        valid_statuses = ["pending", "in_progress", "completed", "blocked", "skipped"]
        if status not in valid_statuses:
            msg = f"Invalid status: {status}. Must be one of: {valid_statuses}"
            raise ValueError(msg)
        self._data["status"] = status
        return self

    def with_agent(self, agent_type: str | None) -> TaskBuilder:
        """Set the agent type (or None for no agent)."""
        self._data["agent_type"] = agent_type
        return self

    def depends_on(self, task_ids: list[str]) -> TaskBuilder:
        """Set task dependencies (list of task IDs)."""
        self._data["depends_on"] = task_ids.copy()
        return self

    def with_priority(self, priority: str | None) -> TaskBuilder:
        """Set task priority.

        Args:
            priority: One of: None, "low", "medium", "high"
        """
        valid_priorities = [None, "low", "medium", "high"]
        if priority not in valid_priorities:
            msg = f"Invalid priority: {priority}. Must be one of: {valid_priorities}"
            raise ValueError(msg)
        self._data["priority"] = priority
        return self

    def with_estimated_minutes(self, minutes: int | None) -> TaskBuilder:
        """Set estimated time in minutes."""
        if minutes is not None and minutes < 0:
            msg = "estimated_minutes must be >= 0"
            raise ValueError(msg)
        self._data["estimated_minutes"] = minutes
        return self

    def started_at(self, timestamp: str) -> TaskBuilder:
        """Set started_at tracking timestamp."""
        if "tracking" not in self._data:
            self._data["tracking"] = {}
        self._data["tracking"]["started_at"] = timestamp
        return self

    def completed_at(self, timestamp: str) -> TaskBuilder:
        """Set completed_at tracking timestamp."""
        if "tracking" not in self._data:
            self._data["tracking"] = {}
        self._data["tracking"]["completed_at"] = timestamp
        return self

    def with_tracking(self, **kwargs) -> TaskBuilder:
        """Set tracking fields directly.

        Args:
            **kwargs: Any tracking fields (started_at, completed_at, time_spent_minutes, etc.)
        """
        if "tracking" not in self._data:
            self._data["tracking"] = {}
        self._data["tracking"].update(kwargs)
        return self

    def with_subtasks(self, subtasks: list[dict[str, Any]]) -> TaskBuilder:
        """Add subtasks to the task."""
        self._data["subtasks"] = subtasks.copy()
        return self

    def build(self) -> dict[str, Any]:
        """Build and return the task dictionary.

        Returns:
            Dict containing the task data
        """
        # Auto-populate tracking timestamps based on status
        if self._data["status"] == "in_progress" and "started_at" not in self._data["tracking"]:
            self._data["tracking"]["started_at"] = "2025-01-01T00:00:00Z"
        elif self._data["status"] == "completed" and "completed_at" not in self._data["tracking"]:
            self._data["tracking"]["completed_at"] = "2025-01-01T00:00:00Z"

        return self._data.copy()


class PhaseBuilder:
    """Builder for Phase test data with fluent interface.

    Automatically calculates progress based on added tasks.
    """

    def __init__(self):
        """Initialize with default phase values."""
        self._data: dict[str, Any] = {
            "id": "0",
            "name": "Test Phase",
            "description": "Test phase description",
            "status": "pending",
            "progress": {
                "completed": 0,
                "total": 0,
                "percentage": 0.0,
            },
            "tasks": [],
        }

    def with_id(self, phase_id: str) -> PhaseBuilder:
        """Set the phase ID."""
        self._data["id"] = phase_id
        return self

    def with_name(self, name: str) -> PhaseBuilder:
        """Set the phase name."""
        self._data["name"] = name
        return self

    def with_description(self, description: str) -> PhaseBuilder:
        """Set the phase description."""
        self._data["description"] = description
        return self

    def with_status(self, status: str) -> PhaseBuilder:
        """Set the phase status.

        Args:
            status: One of: pending, in_progress, completed, blocked, skipped
        """
        valid_statuses = ["pending", "in_progress", "completed", "blocked", "skipped"]
        if status not in valid_statuses:
            msg = f"Invalid status: {status}. Must be one of: {valid_statuses}"
            raise ValueError(msg)
        self._data["status"] = status
        return self

    def add_task(self, task: dict[str, Any]) -> PhaseBuilder:
        """Add a task to the phase.

        Args:
            task: Task dictionary (typically from TaskBuilder.build())
        """
        self._data["tasks"].append(task)
        return self

    def with_tasks(self, tasks: list[dict[str, Any]]) -> PhaseBuilder:
        """Set all tasks at once (replaces existing tasks).

        Args:
            tasks: List of task dictionaries
        """
        self._data["tasks"] = tasks.copy()
        return self

    def _calculate_progress(self) -> None:
        """Calculate progress based on task statuses."""
        tasks = self._data["tasks"]
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "completed")

        self._data["progress"] = {
            "completed": completed,
            "total": total,
            "percentage": round(100 * completed / total, 1) if total > 0 else 0.0,
        }

        # Auto-set phase status based on tasks
        if total == 0:
            self._data["status"] = "pending"
        elif completed == total and total > 0:
            self._data["status"] = "completed"
        elif completed > 0:
            self._data["status"] = "in_progress"

    def build(self) -> dict[str, Any]:
        """Build and return the phase dictionary.

        Automatically calculates progress from tasks.

        Returns:
            Dict containing the phase data
        """
        self._calculate_progress()
        return self._data.copy()


class PlanBuilder:
    """Builder for Plan test data with fluent interface.

    Automatically calculates summary statistics from phases.
    """

    def __init__(self):
        """Initialize with default plan values."""
        self._data: dict[str, Any] = {
            "meta": {
                "project": "Test Project",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "overall_progress": 0.0,
            },
            "phases": [],
        }

    def with_project(self, project_name: str) -> PlanBuilder:
        """Set the project name."""
        self._data["meta"]["project"] = project_name
        return self

    def with_version(self, version: str) -> PlanBuilder:
        """Set the version (must be semver format)."""
        self._data["meta"]["version"] = version
        return self

    def with_schema_version(self, schema_version: str) -> PlanBuilder:
        """Set the schema version."""
        self._data["meta"]["schema_version"] = schema_version
        return self

    def with_business_plan_path(self, path: str) -> PlanBuilder:
        """Set the business plan path."""
        self._data["meta"]["business_plan_path"] = path
        return self

    def with_created_at(self, timestamp: str) -> PlanBuilder:
        """Set the created_at timestamp."""
        self._data["meta"]["created_at"] = timestamp
        return self

    def with_updated_at(self, timestamp: str) -> PlanBuilder:
        """Set the updated_at timestamp."""
        self._data["meta"]["updated_at"] = timestamp
        return self

    def add_phase(self, phase: dict[str, Any]) -> PlanBuilder:
        """Add a phase to the plan.

        Args:
            phase: Phase dictionary (typically from PhaseBuilder.build())
        """
        self._data["phases"].append(phase)
        return self

    def with_phases(self, phases: list[dict[str, Any]]) -> PlanBuilder:
        """Set all phases at once (replaces existing phases).

        Args:
            phases: List of phase dictionaries
        """
        self._data["phases"] = phases.copy()
        return self

    def with_decisions(self, pending: list | None = None, resolved: list | None = None) -> PlanBuilder:
        """Add decision tracking to the plan."""
        self._data["decisions"] = {
            "pending": pending or [],
            "resolved": resolved or [],
        }
        return self

    def with_blockers(self, blockers: list[dict[str, Any]]) -> PlanBuilder:
        """Add blockers to the plan."""
        self._data["blockers"] = blockers.copy()
        return self

    def _calculate_summary(self) -> None:
        """Calculate summary statistics from phases."""
        phases = self._data["phases"]
        total_phases = len(phases)
        total_tasks = sum(len(p.get("tasks", [])) for p in phases)
        completed_tasks = sum(sum(1 for t in p.get("tasks", []) if t.get("status") == "completed") for p in phases)

        self._data["summary"] = {
            "total_phases": total_phases,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overall_progress": round(100 * completed_tasks / total_tasks, 1) if total_tasks > 0 else 0.0,
        }

    def build(self) -> dict[str, Any]:
        """Build and return the plan dictionary.

        Automatically calculates summary from phases.

        Returns:
            Dict containing the complete plan data
        """
        self._calculate_summary()
        return self._data.copy()


# Convenience functions for common scenarios


def build_empty_plan() -> dict[str, Any]:
    """Build an empty plan with no phases."""
    return PlanBuilder().build()


def build_simple_task(task_id: str = "0.1.1", title: str = "Test Task", status: str = "pending") -> dict[str, Any]:
    """Build a simple task with minimal configuration."""
    return TaskBuilder().with_id(task_id).with_title(title).with_status(status).build()


def build_completed_task(task_id: str = "0.1.1", title: str = "Completed Task") -> dict[str, Any]:
    """Build a completed task with timestamp."""
    return (
        TaskBuilder()
        .with_id(task_id)
        .with_title(title)
        .with_status("completed")
        .completed_at("2025-01-01T00:00:00Z")
        .build()
    )


def build_simple_phase(phase_id: str = "0", name: str = "Test Phase", num_tasks: int = 2) -> dict[str, Any]:
    """Build a simple phase with specified number of tasks."""
    builder = PhaseBuilder().with_id(phase_id).with_name(name)

    for i in range(num_tasks):
        task = TaskBuilder().with_id(f"{phase_id}.1.{i + 1}").with_title(f"Task {i + 1}").build()
        builder.add_task(task)

    return builder.build()
