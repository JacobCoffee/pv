"""Shared pytest fixtures for pv-tool tests."""

import json
from argparse import Namespace

import pytest

from tests.builders import PhaseBuilder, PlanBuilder, TaskBuilder


@pytest.fixture
def tmp_plan_path(tmp_path):
    """Return path to a temporary plan.json file."""
    return tmp_path / "plan.json"


@pytest.fixture
def empty_plan():
    """Return a minimal valid plan structure."""
    return {
        "meta": {
            "project": "Test",
            "version": "1.0.0",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
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


@pytest.fixture
def sample_plan():
    """Return a plan with multiple phases and tasks in various states."""
    return {
        "meta": {
            "project": "Test Project",
            "version": "1.0.0",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "business_plan_path": ".claude/BUSINESS_PLAN.md",
        },
        "summary": {
            "total_phases": 2,
            "total_tasks": 4,
            "completed_tasks": 1,
            "overall_progress": 25.0,
        },
        "phases": [
            {
                "id": "0",
                "name": "Setup",
                "description": "Initial setup phase",
                "status": "in_progress",
                "progress": {"completed": 1, "total": 2, "percentage": 50.0},
                "tasks": [
                    {
                        "id": "0.1.1",
                        "title": "Task One",
                        "status": "completed",
                        "agent_type": "python-backend-engineer",
                        "depends_on": [],
                        "tracking": {"completed_at": "2025-01-02T00:00:00Z"},
                    },
                    {
                        "id": "0.1.2",
                        "title": "Task Two",
                        "status": "in_progress",
                        "agent_type": "ui-engineer",
                        "depends_on": ["0.1.1"],
                        "tracking": {"started_at": "2025-01-03T00:00:00Z"},
                    },
                ],
            },
            {
                "id": "1",
                "name": "Development",
                "description": "Main development phase",
                "status": "pending",
                "progress": {"completed": 0, "total": 2, "percentage": 0},
                "tasks": [
                    {
                        "id": "1.1.1",
                        "title": "Feature X",
                        "status": "pending",
                        "agent_type": None,
                        "depends_on": ["0.1.2"],
                        "tracking": {},
                    },
                    {
                        "id": "1.1.2",
                        "title": "Feature Y",
                        "status": "pending",
                        "agent_type": "Python Testing Expert",
                        "depends_on": [],
                        "tracking": {},
                    },
                ],
            },
        ],
    }


@pytest.fixture
def completed_plan():
    """Return a fully completed plan."""
    return {
        "meta": {
            "project": "Completed Project",
            "version": "1.0.0",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "business_plan_path": ".claude/BUSINESS_PLAN.md",
        },
        "summary": {
            "total_phases": 1,
            "total_tasks": 2,
            "completed_tasks": 2,
            "overall_progress": 100.0,
        },
        "phases": [
            {
                "id": "0",
                "name": "Done Phase",
                "description": "All done",
                "status": "completed",
                "progress": {"completed": 2, "total": 2, "percentage": 100.0},
                "tasks": [
                    {
                        "id": "0.1.1",
                        "title": "Done Task 1",
                        "status": "completed",
                        "agent_type": None,
                        "depends_on": [],
                        "tracking": {"completed_at": "2025-01-02T00:00:00Z"},
                    },
                    {
                        "id": "0.1.2",
                        "title": "Done Task 2",
                        "status": "completed",
                        "agent_type": None,
                        "depends_on": [],
                        "tracking": {"completed_at": "2025-01-03T00:00:00Z"},
                    },
                ],
            },
        ],
    }


@pytest.fixture
def plan_with_skipped():
    """Return a plan with skipped phase."""
    return {
        "meta": {
            "project": "Skipped Project",
            "version": "1.0.0",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "business_plan_path": ".claude/BUSINESS_PLAN.md",
        },
        "summary": {
            "total_phases": 1,
            "total_tasks": 1,
            "completed_tasks": 0,
            "overall_progress": 0,
        },
        "phases": [
            {
                "id": "0",
                "name": "Skipped Phase",
                "description": "This was skipped",
                "status": "skipped",
                "progress": {"completed": 0, "total": 1, "percentage": 0},
                "tasks": [
                    {
                        "id": "0.1.1",
                        "title": "Skipped Task",
                        "status": "skipped",
                        "agent_type": None,
                        "depends_on": [],
                        "tracking": {},
                    },
                ],
            },
        ],
    }


@pytest.fixture
def sample_plan_file(tmp_plan_path, sample_plan):
    """Create a temporary plan file with sample data."""
    tmp_plan_path.write_text(json.dumps(sample_plan, indent=2))
    return tmp_plan_path


@pytest.fixture
def empty_plan_file(tmp_plan_path, empty_plan):
    """Create a temporary plan file with minimal data."""
    tmp_plan_path.write_text(json.dumps(empty_plan, indent=2))
    return tmp_plan_path


@pytest.fixture
def base_args(tmp_plan_path):
    """Return base argparse Namespace for edit commands."""
    return Namespace(file=tmp_plan_path, json=False, command=None, help=False)


# ============ BUILDER PATTERN FIXTURES ============


@pytest.fixture
def plan_builder():
    """Return a PlanBuilder instance for fluent test data creation.

    Example:
        def test_something(plan_builder):
            plan = (plan_builder
                    .with_project("My Project")
                    .add_phase(PhaseBuilder().with_id("0").build())
                    .build())
    """
    return PlanBuilder()


@pytest.fixture
def task_builder():
    """Return a TaskBuilder instance for fluent task creation.

    Example:
        def test_something(task_builder):
            task = (task_builder
                    .with_id("1.1.1")
                    .with_title("Test Task")
                    .with_status("completed")
                    .build())
    """
    return TaskBuilder()


@pytest.fixture
def phase_builder():
    """Return a PhaseBuilder instance for fluent phase creation.

    Example:
        def test_something(phase_builder, task_builder):
            phase = (phase_builder
                     .with_id("1")
                     .add_task(task_builder.with_id("1.1.1").build())
                     .build())
    """
    return PhaseBuilder()


# ============ MIGRATED FIXTURES USING BUILDERS ============


@pytest.fixture
def empty_plan_v2(plan_builder):
    """Return an empty plan using the builder pattern.

    This is the builder-based version of empty_plan.
    Use this in new tests for better maintainability.
    """
    return plan_builder.build()


@pytest.fixture
def sample_plan_v2():
    """Return a sample plan with multiple phases using builders.

    This is the builder-based version of sample_plan.
    Use this in new tests for better maintainability.
    """
    # Create tasks for phase 0 (Setup)
    task_0_1_1 = (
        TaskBuilder()
        .with_id("0.1.1")
        .with_title("Task One")
        .with_status("completed")
        .with_agent("python-backend-engineer")
        .completed_at("2025-01-02T00:00:00Z")
        .build()
    )

    task_0_1_2 = (
        TaskBuilder()
        .with_id("0.1.2")
        .with_title("Task Two")
        .with_status("in_progress")
        .with_agent("ui-engineer")
        .depends_on(["0.1.1"])
        .started_at("2025-01-03T00:00:00Z")
        .build()
    )

    # Create phase 0
    phase_0 = (
        PhaseBuilder()
        .with_id("0")
        .with_name("Setup")
        .with_description("Initial setup phase")
        .add_task(task_0_1_1)
        .add_task(task_0_1_2)
        .build()
    )

    # Create tasks for phase 1 (Development)
    task_1_1_1 = (
        TaskBuilder().with_id("1.1.1").with_title("Feature X").with_status("pending").depends_on(["0.1.2"]).build()
    )

    task_1_1_2 = (
        TaskBuilder()
        .with_id("1.1.2")
        .with_title("Feature Y")
        .with_status("pending")
        .with_agent("Python Testing Expert")
        .build()
    )

    # Create phase 1
    phase_1 = (
        PhaseBuilder()
        .with_id("1")
        .with_name("Development")
        .with_description("Main development phase")
        .with_status("pending")
        .add_task(task_1_1_1)
        .add_task(task_1_1_2)
        .build()
    )

    # Create the plan
    return (
        PlanBuilder()
        .with_project("Test Project")
        .with_version("1.0.0")
        .with_created_at("2025-01-01T00:00:00Z")
        .with_updated_at("2025-01-01T00:00:00Z")
        .add_phase(phase_0)
        .add_phase(phase_1)
        .build()
    )


@pytest.fixture
def completed_plan_v2():
    """Return a fully completed plan using builders.

    This is the builder-based version of completed_plan.
    Use this in new tests for better maintainability.
    """
    task_1 = (
        TaskBuilder()
        .with_id("0.1.1")
        .with_title("Done Task 1")
        .with_status("completed")
        .completed_at("2025-01-02T00:00:00Z")
        .build()
    )

    task_2 = (
        TaskBuilder()
        .with_id("0.1.2")
        .with_title("Done Task 2")
        .with_status("completed")
        .completed_at("2025-01-03T00:00:00Z")
        .build()
    )

    phase = (
        PhaseBuilder()
        .with_id("0")
        .with_name("Done Phase")
        .with_description("All done")
        .add_task(task_1)
        .add_task(task_2)
        .build()
    )

    return (
        PlanBuilder()
        .with_project("Completed Project")
        .with_version("1.0.0")
        .with_created_at("2025-01-01T00:00:00Z")
        .with_updated_at("2025-01-01T00:00:00Z")
        .add_phase(phase)
        .build()
    )
