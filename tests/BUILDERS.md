# Test Builder Pattern Documentation

This document describes the builder pattern implementation for creating test fixtures in the pv-tool test suite.

## Overview

The builder pattern provides a fluent, maintainable way to create test data for Tasks, Phases, and Plans. It replaces verbose dictionary literals with chainable methods that have sensible defaults and built-in validation.

## Benefits

- **Readable**: Fluent API makes test data construction self-documenting
- **Maintainable**: Changes to data structure require updates in one place
- **Flexible**: Mix and match defaults with custom values
- **Type-safe**: Validates values at build time
- **Composable**: Builders can be nested (PhaseBuilder uses TaskBuilder, etc.)

## Classes

### TaskBuilder

Creates task dictionaries with sensible defaults.

**Default values:**
- `id`: "0.1.1"
- `title`: "Test Task"
- `status`: "pending"
- `agent_type`: None
- `depends_on`: []
- `tracking`: {}

**Available methods:**

```python
TaskBuilder()
    .with_id(task_id: str)                      # Set task ID (format: X.Y.Z)
    .with_title(title: str)                     # Set task title
    .with_status(status: str)                   # Set status (pending, in_progress, completed, blocked, skipped)
    .with_agent(agent_type: Optional[str])      # Set agent type
    .depends_on(task_ids: List[str])            # Set dependencies
    .with_priority(priority: Optional[str])     # Set priority (None, low, medium, high)
    .with_estimated_minutes(minutes: int)       # Set estimated time
    .started_at(timestamp: str)                 # Set started_at tracking
    .completed_at(timestamp: str)               # Set completed_at tracking
    .with_tracking(**kwargs)                    # Set any tracking fields
    .with_subtasks(subtasks: List[Dict])        # Add subtasks
    .build()                                    # Build and return the task dict
```

**Auto-population:**
- Tasks with `status="in_progress"` automatically get `tracking.started_at` if not set
- Tasks with `status="completed"` automatically get `tracking.completed_at` if not set

**Validation:**
- Status must be one of: pending, in_progress, completed, blocked, skipped
- Priority must be one of: None, low, medium, high
- Estimated minutes must be >= 0

**Examples:**

```python
# Simple pending task
task = TaskBuilder().with_id("1.1.1").with_title("My Task").build()

# Completed task with tracking
task = (
    TaskBuilder()
    .with_id("1.1.1")
    .with_title("Done Task")
    .with_status("completed")
    .completed_at("2025-01-01T00:00:00Z")
    .build()
)

# Task with dependencies and agent
task = (
    TaskBuilder()
    .with_id("1.1.2")
    .with_title("Dependent Task")
    .depends_on(["1.1.1"])
    .with_agent("python-backend-engineer")
    .with_priority("high")
    .with_estimated_minutes(120)
    .build()
)

# Task with custom tracking
task = (
    TaskBuilder()
    .with_id("1.1.3")
    .with_status("in_progress")
    .with_tracking(
        started_at="2025-01-01T10:00:00Z",
        time_spent_minutes=45,
        notes="Made good progress",
        attempts=2
    )
    .build()
)
```

### PhaseBuilder

Creates phase dictionaries with automatic progress calculation.

**Default values:**
- `id`: "0"
- `name`: "Test Phase"
- `description`: "Test phase description"
- `status`: "pending"
- `progress`: Auto-calculated from tasks
- `tasks`: []

**Available methods:**

```python
PhaseBuilder()
    .with_id(phase_id: str)                     # Set phase ID
    .with_name(name: str)                       # Set phase name
    .with_description(description: str)         # Set description
    .with_status(status: str)                   # Set status (pending, in_progress, completed, blocked, skipped)
    .add_task(task: Dict)                       # Add a task to the phase
    .with_tasks(tasks: List[Dict])              # Set all tasks (replaces existing)
    .build()                                    # Build and return the phase dict
```

**Auto-calculation:**
- `progress.total`: Count of tasks
- `progress.completed`: Count of completed tasks
- `progress.percentage`: Percentage of completed tasks (rounded to 1 decimal)
- `status`: Auto-set based on task completion:
  - `pending` if no tasks
  - `completed` if all tasks completed
  - `in_progress` if some tasks completed

**Validation:**
- Status must be one of: pending, in_progress, completed, blocked, skipped

**Examples:**

```python
# Simple phase with tasks
phase = (
    PhaseBuilder()
    .with_id("1")
    .with_name("Development")
    .with_description("Main development phase")
    .add_task(TaskBuilder().with_id("1.1.1").build())
    .add_task(TaskBuilder().with_id("1.1.2").build())
    .build()
)

# Phase with pre-built task list
tasks = [
    TaskBuilder().with_id("2.1.1").with_status("completed").build(),
    TaskBuilder().with_id("2.1.2").with_status("in_progress").build(),
    TaskBuilder().with_id("2.1.3").with_status("pending").build(),
]
phase = (
    PhaseBuilder()
    .with_id("2")
    .with_name("Testing")
    .with_tasks(tasks)
    .build()
)
# This phase will have status="in_progress" and progress 33.3%
```

### PlanBuilder

Creates plan dictionaries with automatic summary calculation.

**Default values:**
- `meta.project`: "Test Project"
- `meta.version`: "1.0.0"
- `meta.created_at`: "2025-01-01T00:00:00Z"
- `meta.updated_at`: "2025-01-01T00:00:00Z"
- `meta.business_plan_path`: ".claude/BUSINESS_PLAN.md"
- `summary`: Auto-calculated from phases
- `phases`: []

**Available methods:**

```python
PlanBuilder()
    .with_project(project_name: str)            # Set project name
    .with_version(version: str)                 # Set version (semver format)
    .with_schema_version(version: str)          # Set schema version
    .with_business_plan_path(path: str)         # Set business plan path
    .with_created_at(timestamp: str)            # Set created_at timestamp
    .with_updated_at(timestamp: str)            # Set updated_at timestamp
    .add_phase(phase: Dict)                     # Add a phase to the plan
    .with_phases(phases: List[Dict])            # Set all phases (replaces existing)
    .with_decisions(pending, resolved)          # Add decision tracking
    .with_blockers(blockers: List[Dict])        # Add blockers
    .build()                                    # Build and return the plan dict
```

**Auto-calculation:**
- `summary.total_phases`: Count of phases
- `summary.total_tasks`: Total tasks across all phases
- `summary.completed_tasks`: Total completed tasks
- `summary.overall_progress`: Overall percentage complete (rounded to 1 decimal)

**Examples:**

```python
# Simple empty plan
plan = PlanBuilder().with_project("My Project").build()

# Complete multi-phase plan
plan = (
    PlanBuilder()
    .with_project("Complex Project")
    .with_version("2.0.0")
    .add_phase(
        PhaseBuilder()
        .with_id("0")
        .with_name("Setup")
        .add_task(TaskBuilder().with_id("0.1.1").with_status("completed").build())
        .build()
    )
    .add_phase(
        PhaseBuilder()
        .with_id("1")
        .with_name("Development")
        .add_task(TaskBuilder().with_id("1.1.1").with_status("in_progress").build())
        .build()
    )
    .build()
)

# Plan with blockers and decisions
blocker = {
    "id": "blocker-1",
    "description": "Waiting for API key",
    "affects_tasks": ["1.1.1"],
    "created_at": "2025-01-01T00:00:00Z",
}

decision = {
    "id": "decision-1",
    "question": "Which framework?",
    "options": ["FastAPI", "Flask"],
    "recommended": "FastAPI",
}

plan = (
    PlanBuilder()
    .with_project("Project with Issues")
    .add_phase(PhaseBuilder().build())
    .with_blockers([blocker])
    .with_decisions(pending=[decision], resolved=[])
    .build()
)
```

## Convenience Functions

For common scenarios, use these shorthand functions:

```python
# Create an empty plan
plan = build_empty_plan()

# Create a simple task
task = build_simple_task("1.1.1", "My Task", "pending")

# Create a completed task with timestamp
task = build_completed_task("1.1.1", "Done Task")

# Create a simple phase with N tasks
phase = build_simple_phase("1", "My Phase", num_tasks=3)
```

## Pytest Fixtures

The following fixtures are available in `conftest.py`:

### Builder Instance Fixtures

```python
def test_something(plan_builder, phase_builder, task_builder):
    """Use builder instances in tests."""
    task = task_builder.with_id("1.1.1").build()
    phase = phase_builder.add_task(task).build()
    plan = plan_builder.add_phase(phase).build()
```

### Pre-built Data Fixtures (v2)

These fixtures use builders internally and are recommended for new tests:

- `empty_plan_v2`: Empty plan with no phases
- `sample_plan_v2`: Multi-phase plan with various task states
- `completed_plan_v2`: Fully completed plan

```python
def test_something(sample_plan_v2):
    """Use pre-built sample plan."""
    assert sample_plan_v2["summary"]["total_tasks"] == 4
```

## Migration Guide

### Old Pattern (Dictionary Literals)

```python
# Old way - verbose and error-prone
@pytest.fixture
def my_plan():
    return {
        "meta": {
            "project": "Test",
            "version": "1.0.0",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "business_plan_path": ".claude/BUSINESS_PLAN.md",
        },
        "summary": {
            "total_phases": 1,
            "total_tasks": 2,
            "completed_tasks": 1,
            "overall_progress": 50.0,
        },
        "phases": [
            {
                "id": "0",
                "name": "Setup",
                "description": "Setup phase",
                "status": "in_progress",
                "progress": {"completed": 1, "total": 2, "percentage": 50.0},
                "tasks": [
                    {
                        "id": "0.1.1",
                        "title": "Task One",
                        "status": "completed",
                        "agent_type": None,
                        "depends_on": [],
                        "tracking": {"completed_at": "2025-01-02T00:00:00Z"},
                    },
                    {
                        "id": "0.1.2",
                        "title": "Task Two",
                        "status": "pending",
                        "agent_type": "tester",
                        "depends_on": ["0.1.1"],
                        "tracking": {},
                    },
                ],
            }
        ],
    }
```

### New Pattern (Builders)

```python
# New way - clear, maintainable, self-documenting
@pytest.fixture
def my_plan():
    task1 = (
        TaskBuilder()
        .with_id("0.1.1")
        .with_title("Task One")
        .with_status("completed")
        .completed_at("2025-01-02T00:00:00Z")
        .build()
    )

    task2 = (
        TaskBuilder()
        .with_id("0.1.2")
        .with_title("Task Two")
        .with_status("pending")
        .with_agent("tester")
        .depends_on(["0.1.1"])
        .build()
    )

    phase = (
        PhaseBuilder()
        .with_id("0")
        .with_name("Setup")
        .with_description("Setup phase")
        .add_task(task1)
        .add_task(task2)
        .build()
    )

    return PlanBuilder().add_phase(phase).build()
```

## Best Practices

1. **Use builders for new fixtures**: Prefer builders over dictionary literals
2. **Keep existing fixtures**: Old fixtures still work; migrate gradually
3. **Use v2 fixtures**: Use `empty_plan_v2`, `sample_plan_v2`, etc. in new tests
4. **Chain methods**: Take advantage of fluent interface for readability
5. **Let builders auto-calculate**: Don't manually set progress/summary fields
6. **Validate early**: Builders validate on `build()`, catching errors early
7. **Document complex fixtures**: Add comments explaining the scenario being tested

## Examples from Real Tests

### Testing Task Status Transitions

```python
def test_status_transition(task_builder):
    """Test task going from pending -> in_progress -> completed."""
    # Start pending
    task = task_builder.with_id("1.1.1").build()
    assert task["status"] == "pending"

    # Transition to in_progress
    task = task_builder.with_status("in_progress").build()
    assert task["status"] == "in_progress"
    assert "started_at" in task["tracking"]

    # Complete
    task = task_builder.with_status("completed").build()
    assert task["status"] == "completed"
    assert "completed_at" in task["tracking"]
```

### Testing Phase Progress Calculation

```python
def test_phase_progress():
    """Test phase progress auto-calculation."""
    tasks = [
        TaskBuilder().with_id("1.1.1").with_status("completed").build(),
        TaskBuilder().with_id("1.1.2").with_status("completed").build(),
        TaskBuilder().with_id("1.1.3").with_status("pending").build(),
        TaskBuilder().with_id("1.1.4").with_status("pending").build(),
    ]

    phase = PhaseBuilder().with_tasks(tasks).build()

    assert phase["progress"]["total"] == 4
    assert phase["progress"]["completed"] == 2
    assert phase["progress"]["percentage"] == 50.0
    assert phase["status"] == "in_progress"
```

### Testing Dependency Chains

```python
def test_task_dependencies():
    """Test task dependency chain."""
    # Create a chain: task1 -> task2 -> task3
    task1 = TaskBuilder().with_id("1.1.1").build()
    task2 = TaskBuilder().with_id("1.1.2").depends_on(["1.1.1"]).build()
    task3 = TaskBuilder().with_id("1.1.3").depends_on(["1.1.2"]).build()

    phase = (
        PhaseBuilder()
        .with_id("1")
        .add_task(task1)
        .add_task(task2)
        .add_task(task3)
        .build()
    )

    assert phase["tasks"][1]["depends_on"] == ["1.1.1"]
    assert phase["tasks"][2]["depends_on"] == ["1.1.2"]
```

### Testing Complex Plans

```python
def test_multi_phase_workflow():
    """Test a realistic multi-phase project workflow."""
    # Setup phase (completed)
    setup = (
        PhaseBuilder()
        .with_id("0")
        .with_name("Setup")
        .add_task(
            TaskBuilder()
            .with_id("0.1.1")
            .with_title("Initialize repository")
            .with_status("completed")
            .build()
        )
        .build()
    )

    # Development phase (in progress)
    dev = (
        PhaseBuilder()
        .with_id("1")
        .with_name("Development")
        .add_task(
            TaskBuilder()
            .with_id("1.1.1")
            .with_title("Implement feature A")
            .with_status("completed")
            .with_agent("python-backend-engineer")
            .build()
        )
        .add_task(
            TaskBuilder()
            .with_id("1.1.2")
            .with_title("Implement feature B")
            .with_status("in_progress")
            .with_agent("python-backend-engineer")
            .depends_on(["1.1.1"])
            .build()
        )
        .build()
    )

    # Testing phase (pending)
    testing = (
        PhaseBuilder()
        .with_id("2")
        .with_name("Testing")
        .add_task(
            TaskBuilder()
            .with_id("2.1.1")
            .with_title("Write tests")
            .with_status("pending")
            .with_agent("Python Testing Expert")
            .depends_on(["1.1.2"])
            .with_priority("high")
            .with_estimated_minutes(120)
            .build()
        )
        .build()
    )

    plan = (
        PlanBuilder()
        .with_project("Multi-Phase Project")
        .add_phase(setup)
        .add_phase(dev)
        .add_phase(testing)
        .build()
    )

    assert plan["summary"]["total_phases"] == 3
    assert plan["summary"]["total_tasks"] == 4
    assert plan["summary"]["completed_tasks"] == 2
    assert plan["summary"]["overall_progress"] == 50.0
```

## Troubleshooting

### Common Issues

**Issue**: Builder methods not chaining
**Solution**: Ensure all methods return `self` (they do by default)

**Issue**: Validation errors on build()
**Solution**: Check that status, priority values are valid

**Issue**: Progress calculation wrong
**Solution**: Don't manually set progress fields; let builders calculate

**Issue**: Changes to data structure break tests
**Solution**: Update builder classes; tests using builders auto-update

## See Also

- `tests/builders.py` - Builder implementations
- `tests/test_builders.py` - Comprehensive builder tests
- `tests/conftest.py` - Fixture definitions
- `src/plan_view/plan.schema.json` - JSON schema for validation
