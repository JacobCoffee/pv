"""Demonstration of builder pattern usage.

This file shows practical examples of using the builder pattern
for creating test fixtures in real-world scenarios.
"""

from tests.builders import PhaseBuilder, PlanBuilder, TaskBuilder


def test_simple_workflow_demo():
    """Demonstrate a simple three-task workflow."""
    # Build a simple plan with a sequential task workflow
    plan = (
        PlanBuilder()
        .with_project("Simple Workflow Demo")
        .add_phase(
            PhaseBuilder()
            .with_id("0")
            .with_name("Implementation")
            .add_task(
                TaskBuilder()
                .with_id("0.1.1")
                .with_title("Write code")
                .with_status("completed")
                .with_agent("python-backend-engineer")
                .completed_at("2025-01-01T10:00:00Z")
                .build()
            )
            .add_task(
                TaskBuilder()
                .with_id("0.1.2")
                .with_title("Write tests")
                .with_status("in_progress")
                .with_agent("Python Testing Expert")
                .depends_on(["0.1.1"])
                .started_at("2025-01-01T11:00:00Z")
                .build()
            )
            .add_task(
                TaskBuilder()
                .with_id("0.1.3")
                .with_title("Deploy")
                .with_status("pending")
                .depends_on(["0.1.2"])
                .with_priority("high")
                .build()
            )
            .build()
        )
        .build()
    )

    # Verify the plan structure
    assert plan["meta"]["project"] == "Simple Workflow Demo"
    assert len(plan["phases"]) == 1
    assert len(plan["phases"][0]["tasks"]) == 3

    # Verify progress calculation
    assert plan["summary"]["total_tasks"] == 3
    assert plan["summary"]["completed_tasks"] == 1
    assert plan["summary"]["overall_progress"] == 33.3

    # Verify dependencies
    assert plan["phases"][0]["tasks"][1]["depends_on"] == ["0.1.1"]
    assert plan["phases"][0]["tasks"][2]["depends_on"] == ["0.1.2"]


def test_agile_sprint_demo():
    """Demonstrate an agile sprint with multiple parallel tasks."""
    # Sprint 1: Backend work
    backend_tasks = [
        TaskBuilder()
        .with_id("0.1.1")
        .with_title("Design API schema")
        .with_status("completed")
        .with_agent("python-backend-engineer")
        .with_estimated_minutes(120)
        .build(),
        TaskBuilder()
        .with_id("0.1.2")
        .with_title("Implement endpoints")
        .with_status("in_progress")
        .with_agent("python-backend-engineer")
        .depends_on(["0.1.1"])
        .with_estimated_minutes(240)
        .build(),
    ]

    # Sprint 1: Frontend work (parallel track)
    frontend_tasks = [
        TaskBuilder()
        .with_id("0.2.1")
        .with_title("Design UI mockups")
        .with_status("completed")
        .with_agent("ui-engineer")
        .with_estimated_minutes(180)
        .build(),
        TaskBuilder()
        .with_id("0.2.2")
        .with_title("Implement components")
        .with_status("in_progress")
        .with_agent("ui-engineer")
        .depends_on(["0.2.1"])
        .with_estimated_minutes(300)
        .build(),
    ]

    # Sprint 1 phase
    sprint1 = (
        PhaseBuilder()
        .with_id("0")
        .with_name("Sprint 1")
        .with_description("Initial feature implementation")
        .with_tasks(backend_tasks + frontend_tasks)
        .build()
    )

    # Integration phase
    integration = (
        PhaseBuilder()
        .with_id("1")
        .with_name("Integration")
        .add_task(
            TaskBuilder()
            .with_id("1.1.1")
            .with_title("Connect frontend to API")
            .with_status("pending")
            .depends_on(["0.1.2", "0.2.2"])
            .with_agent("full-stack-engineer")
            .with_priority("high")
            .build()
        )
        .build()
    )

    # Build the plan
    plan = (
        PlanBuilder()
        .with_project("Agile Sprint Demo")
        .with_version("1.0.0")
        .add_phase(sprint1)
        .add_phase(integration)
        .build()
    )

    # Verify structure
    assert len(plan["phases"]) == 2
    assert len(plan["phases"][0]["tasks"]) == 4
    assert plan["phases"][0]["progress"]["percentage"] == 50.0

    # Verify integration task depends on both tracks
    integration_task = plan["phases"][1]["tasks"][0]
    assert set(integration_task["depends_on"]) == {"0.1.2", "0.2.2"}


def test_blocked_workflow_demo():
    """Demonstrate handling blocked tasks and dependencies."""
    # Create a blocked task scenario
    blocker_info = {
        "id": "blocker-1",
        "description": "Waiting for third-party API credentials",
        "affects_tasks": ["0.1.2"],
        "created_at": "2025-01-01T00:00:00Z",
        "resolved_at": None,
        "resolution": None,
    }

    plan = (
        PlanBuilder()
        .with_project("Blocked Workflow Demo")
        .add_phase(
            PhaseBuilder()
            .with_id("0")
            .with_name("API Integration")
            .add_task(
                TaskBuilder().with_id("0.1.1").with_title("Setup project structure").with_status("completed").build()
            )
            .add_task(
                TaskBuilder()
                .with_id("0.1.2")
                .with_title("Integrate third-party API")
                .with_status("blocked")
                .depends_on(["0.1.1"])
                .with_tracking(notes="Waiting for API credentials from vendor")
                .build()
            )
            .add_task(
                TaskBuilder()
                .with_id("0.1.3")
                .with_title("Write integration tests")
                .with_status("pending")
                .depends_on(["0.1.2"])
                .build()
            )
            .build()
        )
        .with_blockers([blocker_info])
        .build()
    )

    # Verify blocker tracking
    assert len(plan["blockers"]) == 1
    assert plan["blockers"][0]["affects_tasks"] == ["0.1.2"]
    assert plan["phases"][0]["tasks"][1]["status"] == "blocked"


def test_decision_tracking_demo():
    """Demonstrate tracking architectural decisions."""
    # Pending decision
    pending_decision = {
        "id": "decision-1",
        "question": "Which database should we use?",
        "options": ["PostgreSQL", "MySQL", "SQLite"],
        "recommended": "PostgreSQL",
        "business_plan_ref": {
            "section": "Architecture",
            "lines": [45, 60],
            "key_content": "Database selection for production deployment",
        },
    }

    # Resolved decision
    resolved_decision = {
        "id": "decision-2",
        "question": "Which Python framework?",
        "options": ["FastAPI", "Flask", "Django"],
        "recommended": "FastAPI",
        "decided": "FastAPI",
        "decided_at": "2024-12-01T00:00:00Z",
        "decided_by": "Tech Lead",
    }

    plan = (
        PlanBuilder()
        .with_project("Decision Tracking Demo")
        .add_phase(
            PhaseBuilder()
            .with_id("0")
            .with_name("Setup")
            .add_task(
                TaskBuilder()
                .with_id("0.1.1")
                .with_title("Initialize project with chosen framework")
                .with_status("completed")
                .build()
            )
            .add_task(
                TaskBuilder()
                .with_id("0.1.2")
                .with_title("Setup database (pending decision)")
                .with_status("pending")
                .depends_on(["0.1.1"])
                .build()
            )
            .build()
        )
        .with_decisions(pending=[pending_decision], resolved=[resolved_decision])
        .build()
    )

    # Verify decision tracking
    assert len(plan["decisions"]["pending"]) == 1
    assert len(plan["decisions"]["resolved"]) == 1
    assert plan["decisions"]["pending"][0]["recommended"] == "PostgreSQL"
    assert plan["decisions"]["resolved"][0]["decided"] == "FastAPI"


def test_realistic_project_demo():
    """Demonstrate a realistic multi-phase project with all features."""
    # Phase 0: Planning (completed)
    planning = (
        PhaseBuilder()
        .with_id("0")
        .with_name("Planning & Design")
        .add_task(
            TaskBuilder()
            .with_id("0.1.1")
            .with_title("Requirements gathering")
            .with_status("completed")
            .with_agent("product-manager")
            .completed_at("2024-12-01T00:00:00Z")
            .with_tracking(time_spent_minutes=480)
            .build()
        )
        .add_task(
            TaskBuilder()
            .with_id("0.1.2")
            .with_title("Architecture design")
            .with_status("completed")
            .with_agent("architect")
            .depends_on(["0.1.1"])
            .completed_at("2024-12-05T00:00:00Z")
            .with_tracking(time_spent_minutes=360)
            .build()
        )
        .build()
    )

    # Phase 1: Development (in progress)
    development = (
        PhaseBuilder()
        .with_id("1")
        .with_name("Development")
        .add_task(
            TaskBuilder()
            .with_id("1.1.1")
            .with_title("Setup CI/CD pipeline")
            .with_status("completed")
            .with_agent("devops-engineer")
            .completed_at("2024-12-10T00:00:00Z")
            .build()
        )
        .add_task(
            TaskBuilder()
            .with_id("1.1.2")
            .with_title("Implement user authentication")
            .with_status("completed")
            .with_agent("python-backend-engineer")
            .depends_on(["1.1.1"])
            .with_priority("high")
            .completed_at("2024-12-15T00:00:00Z")
            .build()
        )
        .add_task(
            TaskBuilder()
            .with_id("1.1.3")
            .with_title("Build dashboard UI")
            .with_status("in_progress")
            .with_agent("ui-engineer")
            .depends_on(["1.1.2"])
            .with_priority("high")
            .with_estimated_minutes(720)
            .started_at("2024-12-16T00:00:00Z")
            .build()
        )
        .add_task(
            TaskBuilder()
            .with_id("1.1.4")
            .with_title("API documentation")
            .with_status("pending")
            .depends_on(["1.1.2"])
            .with_priority("medium")
            .with_estimated_minutes(240)
            .build()
        )
        .build()
    )

    # Phase 2: Testing (pending)
    testing = (
        PhaseBuilder()
        .with_id("2")
        .with_name("Testing & QA")
        .add_task(
            TaskBuilder()
            .with_id("2.1.1")
            .with_title("Write unit tests")
            .with_status("pending")
            .with_agent("Python Testing Expert")
            .depends_on(["1.1.3", "1.1.4"])
            .with_priority("high")
            .with_estimated_minutes(480)
            .build()
        )
        .add_task(
            TaskBuilder()
            .with_id("2.1.2")
            .with_title("End-to-end testing")
            .with_status("pending")
            .with_agent("qa-engineer")
            .depends_on(["2.1.1"])
            .with_priority("high")
            .with_estimated_minutes(360)
            .build()
        )
        .build()
    )

    # Build complete plan with decisions
    framework_decision = {
        "id": "tech-1",
        "question": "Backend framework?",
        "options": ["FastAPI", "Flask"],
        "decided": "FastAPI",
        "decided_at": "2024-11-15T00:00:00Z",
    }

    plan = (
        PlanBuilder()
        .with_project("E-Commerce Platform")
        .with_version("1.0.0")
        .with_created_at("2024-11-01T00:00:00Z")
        .with_updated_at("2024-12-16T00:00:00Z")
        .add_phase(planning)
        .add_phase(development)
        .add_phase(testing)
        .with_decisions(pending=[], resolved=[framework_decision])
        .build()
    )

    # Verify comprehensive plan structure
    assert plan["meta"]["project"] == "E-Commerce Platform"
    assert len(plan["phases"]) == 3
    assert plan["summary"]["total_tasks"] == 8
    assert plan["summary"]["completed_tasks"] == 4
    assert plan["summary"]["overall_progress"] == 50.0

    # Verify phase statuses
    assert plan["phases"][0]["status"] == "completed"
    assert plan["phases"][1]["status"] == "in_progress"
    assert plan["phases"][2]["status"] == "pending"

    # Verify decisions
    assert len(plan["decisions"]["resolved"]) == 1
    assert plan["decisions"]["resolved"][0]["decided"] == "FastAPI"


def test_builder_fixtures_demo(plan_builder, phase_builder, task_builder):
    """Demonstrate using builder fixtures in tests."""
    # Build test data using fixtures
    task1 = task_builder.with_id("0.1.1").with_title("Fixture Task 1").build()

    task2 = (
        TaskBuilder()  # Can also create new instances
        .with_id("0.1.2")
        .with_title("Fixture Task 2")
        .depends_on([task1["id"]])
        .build()
    )

    phase = phase_builder.with_id("0").add_task(task1).add_task(task2).build()

    plan = plan_builder.with_project("Fixture Demo").add_phase(phase).build()

    # Verify
    assert plan["meta"]["project"] == "Fixture Demo"
    assert len(plan["phases"][0]["tasks"]) == 2


def test_prebuilt_fixture_demo(sample_plan_v2, completed_plan_v2):
    """Demonstrate using pre-built v2 fixtures."""
    # Use sample_plan_v2 for tests needing a realistic multi-phase plan
    assert sample_plan_v2["meta"]["project"] == "Test Project"
    assert len(sample_plan_v2["phases"]) == 2
    assert sample_plan_v2["summary"]["total_tasks"] == 4

    # Use completed_plan_v2 for tests needing a fully completed plan
    assert completed_plan_v2["summary"]["overall_progress"] == 100.0
    assert all(task["status"] == "completed" for phase in completed_plan_v2["phases"] for task in phase["tasks"])
