"""Tests for builder pattern classes.

Demonstrates usage of TaskBuilder, PhaseBuilder, and PlanBuilder
and validates they produce correct data structures.
"""

import pytest

from tests.builders import (
    PhaseBuilder,
    PlanBuilder,
    TaskBuilder,
    build_completed_task,
    build_empty_plan,
    build_simple_phase,
    build_simple_task,
)


class TestTaskBuilder:
    """Tests for TaskBuilder functionality."""

    def test_default_task(self):
        """Test building a task with all defaults."""
        task = TaskBuilder().build()

        assert task["id"] == "0.1.1"
        assert task["title"] == "Test Task"
        assert task["status"] == "pending"
        assert task["agent_type"] is None
        assert task["depends_on"] == []
        assert task["tracking"] == {}

    def test_custom_task(self):
        """Test building a task with custom values."""
        task = (
            TaskBuilder()
            .with_id("1.2.3")
            .with_title("Custom Task")
            .with_status("in_progress")
            .with_agent("python-backend-engineer")
            .build()
        )

        assert task["id"] == "1.2.3"
        assert task["title"] == "Custom Task"
        assert task["status"] == "in_progress"
        assert task["agent_type"] == "python-backend-engineer"

    def test_task_with_dependencies(self):
        """Test task with dependencies."""
        task = TaskBuilder().depends_on(["0.1.1", "0.1.2"]).build()

        assert task["depends_on"] == ["0.1.1", "0.1.2"]

    def test_task_auto_tracking_in_progress(self):
        """Test auto-population of started_at for in_progress tasks."""
        task = TaskBuilder().with_status("in_progress").build()

        assert task["status"] == "in_progress"
        assert "started_at" in task["tracking"]

    def test_task_auto_tracking_completed(self):
        """Test auto-population of completed_at for completed tasks."""
        task = TaskBuilder().with_status("completed").build()

        assert task["status"] == "completed"
        assert "completed_at" in task["tracking"]

    def test_task_manual_tracking_timestamps(self):
        """Test manually setting tracking timestamps."""
        task = (
            TaskBuilder()
            .with_status("completed")
            .started_at("2025-01-01T10:00:00Z")
            .completed_at("2025-01-01T11:00:00Z")
            .build()
        )

        assert task["tracking"]["started_at"] == "2025-01-01T10:00:00Z"
        assert task["tracking"]["completed_at"] == "2025-01-01T11:00:00Z"

    def test_task_with_priority(self):
        """Test setting task priority."""
        task = TaskBuilder().with_priority("high").build()

        assert task["priority"] == "high"

    def test_task_with_estimated_minutes(self):
        """Test setting estimated time."""
        task = TaskBuilder().with_estimated_minutes(120).build()

        assert task["estimated_minutes"] == 120

    def test_task_with_tracking_kwargs(self):
        """Test setting tracking data via kwargs."""
        task = TaskBuilder().with_tracking(time_spent_minutes=45, notes="Test note", attempts=2).build()

        assert task["tracking"]["time_spent_minutes"] == 45
        assert task["tracking"]["notes"] == "Test note"
        assert task["tracking"]["attempts"] == 2

    def test_task_invalid_status(self):
        """Test that invalid status raises error."""
        with pytest.raises(ValueError, match="Invalid status"):
            TaskBuilder().with_status("invalid_status").build()

    def test_task_invalid_priority(self):
        """Test that invalid priority raises error."""
        with pytest.raises(ValueError, match="Invalid priority"):
            TaskBuilder().with_priority("urgent").build()

    def test_task_negative_estimated_minutes(self):
        """Test that negative estimated_minutes raises error."""
        with pytest.raises(ValueError, match="must be >= 0"):
            TaskBuilder().with_estimated_minutes(-10).build()

    def test_task_fluent_chaining(self):
        """Test that all builder methods return self for chaining."""
        task = (
            TaskBuilder()
            .with_id("1.1.1")
            .with_title("Chained")
            .with_status("pending")
            .with_agent("test-agent")
            .depends_on(["0.1.1"])
            .with_priority("medium")
            .with_estimated_minutes(60)
            .build()
        )

        assert task["id"] == "1.1.1"
        assert task["title"] == "Chained"
        assert task["agent_type"] == "test-agent"
        assert task["depends_on"] == ["0.1.1"]
        assert task["priority"] == "medium"
        assert task["estimated_minutes"] == 60


class TestPhaseBuilder:
    """Tests for PhaseBuilder functionality."""

    def test_default_phase(self):
        """Test building a phase with all defaults."""
        phase = PhaseBuilder().build()

        assert phase["id"] == "0"
        assert phase["name"] == "Test Phase"
        assert phase["description"] == "Test phase description"
        assert phase["status"] == "pending"
        assert phase["tasks"] == []
        assert phase["progress"]["total"] == 0
        assert phase["progress"]["completed"] == 0
        assert phase["progress"]["percentage"] == 0.0

    def test_phase_with_single_task(self):
        """Test phase with one task."""
        task = TaskBuilder().with_id("0.1.1").build()
        phase = PhaseBuilder().add_task(task).build()

        assert len(phase["tasks"]) == 1
        assert phase["progress"]["total"] == 1
        assert phase["progress"]["completed"] == 0

    def test_phase_with_multiple_tasks(self):
        """Test phase with multiple tasks."""
        task1 = TaskBuilder().with_id("0.1.1").with_status("completed").build()
        task2 = TaskBuilder().with_id("0.1.2").with_status("pending").build()
        task3 = TaskBuilder().with_id("0.1.3").with_status("in_progress").build()

        phase = PhaseBuilder().add_task(task1).add_task(task2).add_task(task3).build()

        assert len(phase["tasks"]) == 3
        assert phase["progress"]["total"] == 3
        assert phase["progress"]["completed"] == 1
        assert phase["progress"]["percentage"] == 33.3

    def test_phase_auto_status_completed(self):
        """Test phase auto-sets status to completed when all tasks done."""
        task1 = TaskBuilder().with_status("completed").build()
        task2 = TaskBuilder().with_status("completed").build()

        phase = PhaseBuilder().add_task(task1).add_task(task2).build()

        assert phase["status"] == "completed"
        assert phase["progress"]["percentage"] == 100.0

    def test_phase_auto_status_in_progress(self):
        """Test phase auto-sets status to in_progress when partially done."""
        task1 = TaskBuilder().with_status("completed").build()
        task2 = TaskBuilder().with_status("pending").build()

        phase = PhaseBuilder().add_task(task1).add_task(task2).build()

        assert phase["status"] == "in_progress"

    def test_phase_with_tasks_replaces_existing(self):
        """Test with_tasks replaces existing tasks."""
        task1 = TaskBuilder().with_id("0.1.1").build()
        task2 = TaskBuilder().with_id("0.1.2").build()
        task3 = TaskBuilder().with_id("0.1.3").build()

        phase = (
            PhaseBuilder()
            .add_task(task1)
            .with_tasks([task2, task3])  # Replaces task1
            .build()
        )

        assert len(phase["tasks"]) == 2
        assert phase["tasks"][0]["id"] == "0.1.2"
        assert phase["tasks"][1]["id"] == "0.1.3"

    def test_phase_custom_values(self):
        """Test phase with custom metadata."""
        phase = PhaseBuilder().with_id("5").with_name("Custom Phase").with_description("Custom description").build()

        assert phase["id"] == "5"
        assert phase["name"] == "Custom Phase"
        assert phase["description"] == "Custom description"

    def test_phase_invalid_status(self):
        """Test that invalid status raises error."""
        with pytest.raises(ValueError, match="Invalid status"):
            PhaseBuilder().with_status("unknown").build()


class TestPlanBuilder:
    """Tests for PlanBuilder functionality."""

    def test_default_plan(self):
        """Test building a plan with all defaults."""
        plan = PlanBuilder().build()

        assert plan["meta"]["project"] == "Test Project"
        assert plan["meta"]["version"] == "1.0.0"
        assert plan["meta"]["business_plan_path"] == ".claude/BUSINESS_PLAN.md"
        assert plan["phases"] == []
        assert plan["summary"]["total_phases"] == 0
        assert plan["summary"]["total_tasks"] == 0
        assert plan["summary"]["completed_tasks"] == 0
        assert plan["summary"]["overall_progress"] == 0.0

    def test_plan_with_single_phase(self):
        """Test plan with one phase."""
        phase = PhaseBuilder().with_id("0").build()
        plan = PlanBuilder().add_phase(phase).build()

        assert len(plan["phases"]) == 1
        assert plan["summary"]["total_phases"] == 1

    def test_plan_with_multiple_phases(self):
        """Test plan with multiple phases and tasks."""
        task1 = TaskBuilder().with_id("0.1.1").with_status("completed").build()
        task2 = TaskBuilder().with_id("0.1.2").with_status("pending").build()

        phase1 = PhaseBuilder().with_id("0").add_task(task1).build()
        phase2 = PhaseBuilder().with_id("1").add_task(task2).build()

        plan = PlanBuilder().add_phase(phase1).add_phase(phase2).build()

        assert len(plan["phases"]) == 2
        assert plan["summary"]["total_phases"] == 2
        assert plan["summary"]["total_tasks"] == 2
        assert plan["summary"]["completed_tasks"] == 1
        assert plan["summary"]["overall_progress"] == 50.0

    def test_plan_custom_metadata(self):
        """Test plan with custom metadata."""
        plan = (
            PlanBuilder()
            .with_project("Custom Project")
            .with_version("2.5.0")
            .with_schema_version("1.0.0")
            .with_business_plan_path("custom/path.md")
            .with_created_at("2024-01-01T00:00:00Z")
            .with_updated_at("2024-12-31T23:59:59Z")
            .build()
        )

        assert plan["meta"]["project"] == "Custom Project"
        assert plan["meta"]["version"] == "2.5.0"
        assert plan["meta"]["schema_version"] == "1.0.0"
        assert plan["meta"]["business_plan_path"] == "custom/path.md"
        assert plan["meta"]["created_at"] == "2024-01-01T00:00:00Z"
        assert plan["meta"]["updated_at"] == "2024-12-31T23:59:59Z"

    def test_plan_with_decisions(self):
        """Test plan with decision tracking."""
        pending_decision = {
            "id": "decision-1",
            "question": "Which framework?",
            "options": ["FastAPI", "Flask"],
        }

        plan = PlanBuilder().with_decisions(pending=[pending_decision], resolved=[]).build()

        assert "decisions" in plan
        assert len(plan["decisions"]["pending"]) == 1
        assert plan["decisions"]["pending"][0]["id"] == "decision-1"

    def test_plan_with_blockers(self):
        """Test plan with blockers."""
        blocker = {
            "id": "blocker-1",
            "description": "API key needed",
            "affects_tasks": ["0.1.1"],
            "created_at": "2025-01-01T00:00:00Z",
        }

        plan = PlanBuilder().with_blockers([blocker]).build()

        assert "blockers" in plan
        assert len(plan["blockers"]) == 1
        assert plan["blockers"][0]["id"] == "blocker-1"

    def test_plan_with_phases_replaces_existing(self):
        """Test with_phases replaces existing phases."""
        phase1 = PhaseBuilder().with_id("0").build()
        phase2 = PhaseBuilder().with_id("1").build()
        phase3 = PhaseBuilder().with_id("2").build()

        plan = (
            PlanBuilder()
            .add_phase(phase1)
            .with_phases([phase2, phase3])  # Replaces phase1
            .build()
        )

        assert len(plan["phases"]) == 2
        assert plan["phases"][0]["id"] == "1"
        assert plan["phases"][1]["id"] == "2"


class TestConvenienceFunctions:
    """Tests for convenience builder functions."""

    def test_build_empty_plan(self):
        """Test build_empty_plan convenience function."""
        plan = build_empty_plan()

        assert plan["summary"]["total_tasks"] == 0
        assert plan["phases"] == []

    def test_build_simple_task(self):
        """Test build_simple_task convenience function."""
        task = build_simple_task("1.2.3", "My Task", "pending")

        assert task["id"] == "1.2.3"
        assert task["title"] == "My Task"
        assert task["status"] == "pending"

    def test_build_completed_task(self):
        """Test build_completed_task convenience function."""
        task = build_completed_task("2.3.4", "Done Task")

        assert task["id"] == "2.3.4"
        assert task["title"] == "Done Task"
        assert task["status"] == "completed"
        assert "completed_at" in task["tracking"]

    def test_build_simple_phase(self):
        """Test build_simple_phase convenience function."""
        phase = build_simple_phase("3", "My Phase", 4)

        assert phase["id"] == "3"
        assert phase["name"] == "My Phase"
        assert len(phase["tasks"]) == 4
        assert phase["tasks"][0]["id"] == "3.1.1"
        assert phase["tasks"][3]["id"] == "3.1.4"


class TestBuilderFixtures:
    """Tests for builder-based fixtures in conftest.py."""

    def test_plan_builder_fixture(self, plan_builder):
        """Test plan_builder fixture provides a fresh builder."""
        plan = plan_builder.with_project("Fixture Test").build()

        assert plan["meta"]["project"] == "Fixture Test"

    def test_task_builder_fixture(self, task_builder):
        """Test task_builder fixture provides a fresh builder."""
        task = task_builder.with_title("Fixture Task").build()

        assert task["title"] == "Fixture Task"

    def test_phase_builder_fixture(self, phase_builder):
        """Test phase_builder fixture provides a fresh builder."""
        phase = phase_builder.with_name("Fixture Phase").build()

        assert phase["name"] == "Fixture Phase"

    def test_empty_plan_v2_fixture(self, empty_plan_v2):
        """Test empty_plan_v2 fixture produces valid empty plan."""
        assert empty_plan_v2["summary"]["total_tasks"] == 0
        assert empty_plan_v2["phases"] == []

    def test_sample_plan_v2_fixture(self, sample_plan_v2):
        """Test sample_plan_v2 fixture produces valid sample plan."""
        assert sample_plan_v2["meta"]["project"] == "Test Project"
        assert len(sample_plan_v2["phases"]) == 2
        assert sample_plan_v2["summary"]["total_tasks"] == 4
        assert sample_plan_v2["summary"]["completed_tasks"] == 1

    def test_completed_plan_v2_fixture(self, completed_plan_v2):
        """Test completed_plan_v2 fixture produces fully completed plan."""
        assert completed_plan_v2["meta"]["project"] == "Completed Project"
        assert len(completed_plan_v2["phases"]) == 1
        assert completed_plan_v2["summary"]["overall_progress"] == 100.0


class TestComplexBuilderScenarios:
    """Tests for complex real-world builder scenarios."""

    def test_multi_phase_project(self):
        """Test building a complex multi-phase project."""
        # Phase 0: Setup (completed)
        setup_tasks = [
            TaskBuilder().with_id("0.1.1").with_title("Init repo").with_status("completed").build(),
            TaskBuilder().with_id("0.1.2").with_title("Setup CI").with_status("completed").build(),
        ]
        setup = PhaseBuilder().with_id("0").with_name("Setup").with_tasks(setup_tasks).build()

        # Phase 1: Development (in progress)
        dev_tasks = [
            TaskBuilder()
            .with_id("1.1.1")
            .with_title("Implement feature A")
            .with_status("completed")
            .with_agent("python-backend-engineer")
            .build(),
            TaskBuilder()
            .with_id("1.1.2")
            .with_title("Implement feature B")
            .with_status("in_progress")
            .with_agent("python-backend-engineer")
            .depends_on(["1.1.1"])
            .build(),
        ]
        dev = PhaseBuilder().with_id("1").with_name("Development").with_tasks(dev_tasks).build()

        # Phase 2: Testing (pending)
        test_tasks = [
            TaskBuilder()
            .with_id("2.1.1")
            .with_title("Write tests")
            .with_status("pending")
            .with_agent("Python Testing Expert")
            .depends_on(["1.1.2"])
            .with_priority("high")
            .with_estimated_minutes(120)
            .build(),
        ]
        testing = PhaseBuilder().with_id("2").with_name("Testing").with_tasks(test_tasks).build()

        # Build complete plan
        plan = (
            PlanBuilder()
            .with_project("Multi-Phase Project")
            .with_version("1.0.0")
            .add_phase(setup)
            .add_phase(dev)
            .add_phase(testing)
            .build()
        )

        assert len(plan["phases"]) == 3
        assert plan["summary"]["total_tasks"] == 5
        assert plan["summary"]["completed_tasks"] == 3
        assert plan["summary"]["overall_progress"] == 60.0

    def test_plan_with_blockers_and_decisions(self):
        """Test building a plan with blockers and decisions."""
        task = TaskBuilder().with_id("0.1.1").with_status("blocked").build()
        phase = PhaseBuilder().with_id("0").add_task(task).build()

        blocker = {
            "id": "blocker-1",
            "description": "Waiting for API access",
            "affects_tasks": ["0.1.1"],
            "created_at": "2025-01-01T00:00:00Z",
            "resolved_at": None,
            "resolution": None,
        }

        decision = {
            "id": "decision-1",
            "question": "Which database to use?",
            "options": ["PostgreSQL", "MySQL", "SQLite"],
            "recommended": "PostgreSQL",
        }

        plan = (
            PlanBuilder()
            .with_project("Complex Project")
            .add_phase(phase)
            .with_blockers([blocker])
            .with_decisions(pending=[decision])
            .build()
        )

        assert len(plan["blockers"]) == 1
        assert plan["blockers"][0]["affects_tasks"] == ["0.1.1"]
        assert len(plan["decisions"]["pending"]) == 1
        assert plan["decisions"]["pending"][0]["recommended"] == "PostgreSQL"
