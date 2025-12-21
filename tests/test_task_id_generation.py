"""Parametric tests for task ID generation logic.

This module tests the task ID generation algorithm used when adding new tasks
to a phase. Task IDs follow the format: phase.section.task (e.g., "1.2.3").

The ID generation logic (from commands/edit.py):
1. For empty phases: generates "phase_id.1.1"
2. For non-empty phases: finds max section and task numbers, then generates
   "phase_id.max_section.max_task+1"
"""

import json
from argparse import Namespace

import pytest

from plan_view import cli


class TestTaskIDGeneration:
    """Parametric tests for task ID generation in various scenarios."""

    @pytest.mark.parametrize(
        "phase_id,existing_task_ids,expected_new_id,description",
        [
            # Empty phase scenarios
            ("0", [], "0.1.1", "First task in empty phase"),
            ("1", [], "1.1.1", "First task in phase 1"),
            ("5", [], "5.1.1", "First task in phase 5"),
            ("999", [], "999.1.1", "First task in phase with large ID"),
            # Single task scenarios
            ("0", ["0.1.1"], "0.1.2", "Second task in section 1"),
            ("0", ["0.1.5"], "0.1.6", "Task after non-sequential ID"),
            ("0", ["0.2.1"], "0.2.2", "Task in section 2"),
            # Multiple tasks in same section
            ("0", ["0.1.1", "0.1.2"], "0.1.3", "Sequential tasks in section 1"),
            ("0", ["0.1.1", "0.1.2", "0.1.3"], "0.1.4", "Three sequential tasks"),
            ("0", ["0.2.1", "0.2.2", "0.2.3"], "0.2.4", "Sequential tasks in section 2"),
            # Non-sequential task numbers (gaps)
            ("0", ["0.1.1", "0.1.3"], "0.1.4", "Gap in task numbers (missing 0.1.2)"),
            ("0", ["0.1.1", "0.1.5", "0.1.3"], "0.1.6", "Out-of-order tasks with gaps"),
            ("0", ["0.1.10", "0.1.2"], "0.1.11", "Large gap in task numbers"),
            # Multiple sections
            ("0", ["0.1.1", "0.2.1"], "0.2.2", "Tasks in different sections (max is section 2)"),
            ("0", ["0.2.1", "0.1.1"], "0.2.2", "Out-of-order sections"),
            ("0", ["0.1.5", "0.2.1"], "0.2.2", "Multiple sections, max in higher section"),
            ("0", ["0.1.1", "0.2.5"], "0.2.6", "Max task in higher section"),
            # Edge cases with section numbers
            ("0", ["0.1.1", "0.3.1"], "0.3.2", "Skipped section 2"),
            ("0", ["0.1.1", "0.2.1", "0.3.1"], "0.3.2", "Three sections"),
            # Boundary testing - large numbers
            ("0", ["0.1.99"], "0.1.100", "Large task number"),
            ("0", ["0.99.1"], "0.99.2", "Large section number"),
            ("0", ["0.50.50"], "0.50.51", "Large section and task numbers"),
            # Mixed scenarios
            ("0", ["0.1.1", "0.1.2", "0.2.1"], "0.2.2", "Mixed sections, max in section 2"),
            (
                "0",
                ["0.1.1", "0.1.3", "0.2.1", "0.2.2"],
                "0.2.3",
                "Multiple sections with gaps",
            ),
            (
                "0",
                ["0.1.5", "0.2.3", "0.3.1"],
                "0.3.2",
                "Three sections with varying task counts",
            ),
            # Out of order insertion scenarios
            ("0", ["0.1.3", "0.1.1", "0.1.2"], "0.1.4", "Out-of-order task list"),
            (
                "0",
                ["0.2.2", "0.1.1", "0.2.1"],
                "0.2.3",
                "Out-of-order sections and tasks",
            ),
        ],
    )
    def test_task_id_generation(
        self,
        tmp_plan_path,
        phase_id,
        existing_task_ids,
        expected_new_id,
        description,
    ):
        """Test task ID generation with various existing task configurations.

        Tests the ID generation algorithm which should:
        - Return "phase.1.1" for empty phases
        - Find max section and task numbers and increment task number
        - Handle gaps, out-of-order IDs, and multiple sections correctly
        """
        # Create plan with phase containing existing tasks
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": phase_id,
                    "name": "Test Phase",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": len(existing_task_ids), "percentage": 0},
                    "tasks": [
                        {
                            "id": task_id,
                            "title": f"Task {task_id}",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        }
                        for task_id in existing_task_ids
                    ],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        # Add a new task
        args = Namespace(
            file=tmp_plan_path,
            phase=phase_id,
            title="New Task",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )
        cli.cmd_add_task(args)

        # Verify the new task has the expected ID
        result_plan = json.loads(tmp_plan_path.read_text())
        new_task = result_plan["phases"][0]["tasks"][-1]
        assert new_task["id"] == expected_new_id, f"Test case: {description}"

    @pytest.mark.parametrize(
        "malformed_ids,expected_new_id,description",
        [
            # Malformed IDs with fewer than 3 parts are skipped, defaults to 0.0.1
            (["0.1"], "0.0.1", "Single malformed ID with 2 parts - defaults to 0.0.1"),
            (["0"], "0.0.1", "Single malformed ID with 1 part - defaults to 0.0.1"),
            (["invalid"], "0.0.1", "Non-numeric malformed ID - defaults to 0.0.1"),
            # Mix of malformed and valid IDs - valid IDs are processed
            (["0.1", "0.1.1"], "0.1.2", "Mix of malformed and valid IDs - uses valid"),
            (["0.1.1", "0.2"], "0.1.2", "Valid ID followed by malformed - uses valid"),
            (["short", "0.1.1"], "0.1.2", "Completely malformed followed by valid - uses valid"),
            # Multiple malformed IDs only - all skipped
            (["0.1", "0.2"], "0.0.1", "Multiple malformed IDs - defaults to 0.0.1"),
            (["0", "1", "2"], "0.0.1", "Only single-part IDs - defaults to 0.0.1"),
        ],
    )
    def test_task_id_generation_malformed_ids(
        self,
        tmp_plan_path,
        malformed_ids,
        expected_new_id,
        description,
    ):
        """Test task ID generation handles malformed existing task IDs gracefully.

        When existing tasks have malformed IDs (< 3 parts), the algorithm skips them.
        If all IDs are malformed (none with >= 3 parts), max_section and max_task
        remain 0, resulting in "phase.0.1" being generated.

        Note: Non-numeric parts will cause ValueError and are tested separately.
        """
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": len(malformed_ids), "percentage": 0},
                    "tasks": [
                        {
                            "id": task_id,
                            "title": f"Task {task_id}",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        }
                        for task_id in malformed_ids
                    ],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        args = Namespace(
            file=tmp_plan_path,
            phase="0",
            title="New Task",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )
        cli.cmd_add_task(args)

        result_plan = json.loads(tmp_plan_path.read_text())
        new_task = result_plan["phases"][0]["tasks"][-1]
        assert new_task["id"] == expected_new_id, f"Test case: {description}"

    @pytest.mark.parametrize(
        "invalid_ids,description",
        [
            (["0.x.y"], "Non-numeric section and task parts"),
            (["0.1.x"], "Non-numeric task part"),
            (["0.x.1"], "Non-numeric section part"),
        ],
    )
    def test_task_id_generation_non_numeric_parts_error(
        self,
        tmp_plan_path,
        invalid_ids,
        description,
    ):
        """Test that non-numeric parts in task IDs cause ValueError.

        The current implementation tries to convert parts[1] and parts[2] to int
        without error handling. Non-numeric values will raise ValueError.

        This test documents the current behavior (error on invalid data).
        """
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": len(invalid_ids), "percentage": 0},
                    "tasks": [
                        {
                            "id": task_id,
                            "title": f"Task {task_id}",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        }
                        for task_id in invalid_ids
                    ],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        args = Namespace(
            file=tmp_plan_path,
            phase="0",
            title="New Task",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )

        # Should raise ValueError when trying to int() non-numeric parts
        with pytest.raises(ValueError, match="invalid literal for int"):
            cli.cmd_add_task(args)

    @pytest.mark.parametrize(
        "phase_count,expected_first_ids",
        [
            (1, ["0.1.1"]),
            (3, ["0.1.1", "1.1.1", "2.1.1"]),
            (5, ["0.1.1", "1.1.1", "2.1.1", "3.1.1", "4.1.1"]),
            (10, ["0.1.1", "1.1.1", "2.1.1", "3.1.1", "4.1.1", "5.1.1", "6.1.1", "7.1.1", "8.1.1", "9.1.1"]),
        ],
    )
    def test_task_id_generation_multiple_empty_phases(
        self,
        tmp_plan_path,
        phase_count,
        expected_first_ids,
    ):
        """Test adding first task to multiple empty phases.

        Ensures that the phase ID is correctly used in the generated task ID
        for each phase.
        """
        # Create plan with multiple empty phases
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": str(i),
                    "name": f"Phase {i}",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                }
                for i in range(phase_count)
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        # Add task to each phase and verify IDs
        for i in range(phase_count):
            args = Namespace(
                file=tmp_plan_path,
                phase=str(i),
                title=f"First task in phase {i}",
                agent=None,
                deps=None,
                quiet=True,
                dry_run=False,
            )
            cli.cmd_add_task(args)

        # Verify all task IDs
        result_plan = json.loads(tmp_plan_path.read_text())
        for i in range(phase_count):
            first_task = result_plan["phases"][i]["tasks"][0]
            assert first_task["id"] == expected_first_ids[i]

    @pytest.mark.parametrize(
        "task_count,expected_last_id",
        [
            (1, "0.1.1"),
            (5, "0.1.5"),
            (10, "0.1.10"),
            (50, "0.1.50"),
            (100, "0.1.100"),
        ],
    )
    def test_task_id_generation_sequential_additions(
        self,
        tmp_plan_path,
        task_count,
        expected_last_id,
    ):
        """Test sequential task additions generate correct incremental IDs.

        Simulates adding many tasks one after another to ensure IDs
        increment correctly.
        """
        # Start with empty phase
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        # Add tasks sequentially
        for i in range(task_count):
            args = Namespace(
                file=tmp_plan_path,
                phase="0",
                title=f"Task {i+1}",
                agent=None,
                deps=None,
                quiet=True,
                dry_run=False,
            )
            cli.cmd_add_task(args)

        # Verify last task has correct ID
        result_plan = json.loads(tmp_plan_path.read_text())
        assert len(result_plan["phases"][0]["tasks"]) == task_count
        last_task = result_plan["phases"][0]["tasks"][-1]
        assert last_task["id"] == expected_last_id

        # Verify all IDs are sequential
        for i, task in enumerate(result_plan["phases"][0]["tasks"]):
            assert task["id"] == f"0.1.{i+1}"


class TestTaskIDGenerationEdgeCases:
    """Edge case tests for task ID generation."""

    def test_empty_phase_first_task(self, tmp_plan_path):
        """Test generating ID for very first task in empty phase."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "0",
                    "name": "Empty",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        args = Namespace(
            file=tmp_plan_path,
            phase="0",
            title="First Ever Task",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )
        cli.cmd_add_task(args)

        result_plan = json.loads(tmp_plan_path.read_text())
        assert len(result_plan["phases"][0]["tasks"]) == 1
        assert result_plan["phases"][0]["tasks"][0]["id"] == "0.1.1"

    def test_max_section_with_lower_task_number(self, tmp_plan_path):
        """Test that max section is chosen even if it has lower task numbers.

        Example: Tasks "0.1.5" and "0.2.1" exist.
        New task should be "0.2.2" (section 2 is max, even though task 1 < 5).
        """
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "0",
                    "name": "Test",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.5",
                            "title": "Section 1, Task 5",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "0.2.1",
                            "title": "Section 2, Task 1",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                    ],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        args = Namespace(
            file=tmp_plan_path,
            phase="0",
            title="New Task",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )
        cli.cmd_add_task(args)

        result_plan = json.loads(tmp_plan_path.read_text())
        new_task = result_plan["phases"][0]["tasks"][-1]
        assert new_task["id"] == "0.2.2"

    def test_same_section_multiple_tasks_unordered(self, tmp_plan_path):
        """Test task number increment with unordered task list.

        Tasks in same section but added in random order should still
        generate correct next ID based on max task number.
        """
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "0",
                    "name": "Test",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 3, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.3",
                            "title": "Task 3 (added first)",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.1",
                            "title": "Task 1 (added second)",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Task 2 (added third)",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                    ],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        args = Namespace(
            file=tmp_plan_path,
            phase="0",
            title="New Task",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )
        cli.cmd_add_task(args)

        result_plan = json.loads(tmp_plan_path.read_text())
        new_task = result_plan["phases"][0]["tasks"][-1]
        # Should be 0.1.4 (max task was 3)
        assert new_task["id"] == "0.1.4"

    def test_deferred_phase_id_generation(self, tmp_plan_path):
        """Test task ID generation in special 'deferred' phase.

        The deferred phase uses a different ID pattern but should still
        follow the same generation logic.
        """
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "deferred",
                    "name": "Deferred",
                    "description": "Deferred tasks",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        args = Namespace(
            file=tmp_plan_path,
            phase="deferred",
            title="First deferred task",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )
        cli.cmd_add_task(args)

        result_plan = json.loads(tmp_plan_path.read_text())
        new_task = result_plan["phases"][0]["tasks"][0]
        assert new_task["id"] == "deferred.1.1"

    def test_string_phase_id(self, tmp_plan_path):
        """Test task ID generation with non-numeric phase IDs.

        Phase IDs can be strings (like 'deferred'), not just numbers.
        """
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "custom-phase",
                    "name": "Custom",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        args = Namespace(
            file=tmp_plan_path,
            phase="custom-phase",
            title="Task in custom phase",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )
        cli.cmd_add_task(args)

        result_plan = json.loads(tmp_plan_path.read_text())
        new_task = result_plan["phases"][0]["tasks"][0]
        assert new_task["id"] == "custom-phase.1.1"


class TestTaskIDGenerationBoundaries:
    """Boundary value tests for task ID generation."""

    @pytest.mark.parametrize(
        "last_task_number,expected_new_number",
        [
            (0, 1),  # Edge case: task number 0 (shouldn't happen but handle it)
            (1, 2),  # Normal case: increment from 1
            (99, 100),  # Boundary: two to three digits
            (999, 1000),  # Boundary: three to four digits
            (9999, 10000),  # Large boundary
        ],
    )
    def test_task_number_boundaries(self, tmp_plan_path, last_task_number, expected_new_number):
        """Test task number increment at digit boundaries."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "0",
                    "name": "Test",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                    "tasks": [
                        {
                            "id": f"0.1.{last_task_number}",
                            "title": f"Task {last_task_number}",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        }
                    ],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        args = Namespace(
            file=tmp_plan_path,
            phase="0",
            title="New Task",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )
        cli.cmd_add_task(args)

        result_plan = json.loads(tmp_plan_path.read_text())
        new_task = result_plan["phases"][0]["tasks"][-1]
        assert new_task["id"] == f"0.1.{expected_new_number}"

    @pytest.mark.parametrize(
        "last_section_number,expected_new_section",
        [
            (1, 1),  # Normal: stays in same section, increments task
            (99, 99),  # Large section number
            (999, 999),  # Very large section number
        ],
    )
    def test_section_number_boundaries(self, tmp_plan_path, last_section_number, expected_new_section):
        """Test section numbers at digit boundaries.

        Note: New tasks are added to the max section, incrementing task number.
        This tests that large section numbers are handled correctly.
        """
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {},
            "phases": [
                {
                    "id": "0",
                    "name": "Test",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                    "tasks": [
                        {
                            "id": f"0.{last_section_number}.1",
                            "title": f"Section {last_section_number}",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        }
                    ],
                }
            ],
        }

        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        args = Namespace(
            file=tmp_plan_path,
            phase="0",
            title="New Task",
            agent=None,
            deps=None,
            quiet=True,
            dry_run=False,
        )
        cli.cmd_add_task(args)

        result_plan = json.loads(tmp_plan_path.read_text())
        new_task = result_plan["phases"][0]["tasks"][-1]
        # Should increment task number in same section
        assert new_task["id"] == f"0.{expected_new_section}.2"
