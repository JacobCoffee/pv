"""Tests for task dependency validation and circular dependency detection.

This module tests dependency-related functionality including:
- Direct circular dependencies (A->B->A)
- Transitive circular dependencies (A->B->C->A)
- Non-existent task references
- Valid dependency chains
"""

import json
from argparse import Namespace

from plan_view import cli


class TestCircularDependencies:
    """Tests for circular dependency detection."""

    def test_direct_circular_dependency_two_tasks(self, tmp_plan_path):
        """Test detection of direct circular dependency: A depends on B, B depends on A.

        This is the simplest form of circular dependency where two tasks
        directly depend on each other, creating an impossible situation.
        """
        plan = {
            "meta": {
                "project": "Circular Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 2,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with circular deps",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Task A",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.2"],  # A depends on B
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Task B",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],  # B depends on A - CIRCULAR!
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        # The schema validation should pass (format is correct)
        # but semantically this is invalid
        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # Neither task should be actionable since they depend on each other
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is None, "No task should be actionable with circular dependencies"

    def test_direct_circular_dependency_self_reference(self, tmp_plan_path):
        """Test detection of task depending on itself.

        This is a degenerate case of circular dependency where a task
        directly references itself in its depends_on list.
        """
        plan = {
            "meta": {
                "project": "Self Reference Test",
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
                    "name": "Test Phase",
                    "description": "Phase with self-referencing task",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Self Referencing Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],  # Task depends on itself!
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # Task should not be actionable since it depends on itself
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is None, "Task with self-reference should not be actionable"

    def test_transitive_circular_dependency_three_tasks(self, tmp_plan_path):
        """Test detection of transitive circular dependency: A->B->C->A.

        This tests a more complex circular dependency where the cycle
        involves three tasks in a chain that loops back to the start.
        """
        plan = {
            "meta": {
                "project": "Transitive Circular Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 3,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with transitive circular deps",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 3, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Task A",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.2"],  # A depends on B
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Task B",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.3"],  # B depends on C
                            "tracking": {},
                        },
                        {
                            "id": "0.1.3",
                            "title": "Task C",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],  # C depends on A - CIRCULAR!
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # No task should be actionable in this circular chain
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is None, "No task should be actionable with transitive circular dependencies"

    def test_transitive_circular_dependency_long_chain(self, tmp_plan_path):
        """Test detection of circular dependency in longer chain: A->B->C->D->E->A.

        This tests circular dependency detection with a longer dependency chain
        to ensure the algorithm can handle more complex cycles.
        """
        plan = {
            "meta": {
                "project": "Long Chain Circular Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 5,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with long circular chain",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 5, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Task A",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.2"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Task B",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.3"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.3",
                            "title": "Task C",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.4"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.4",
                            "title": "Task D",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.5"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.5",
                            "title": "Task E",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],  # E depends on A - CIRCULAR!
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # No task should be actionable in this long circular chain
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is None, "No task should be actionable with long circular chain"

    def test_partial_circular_with_independent_task(self, tmp_plan_path):
        """Test that independent tasks remain actionable despite circular deps elsewhere.

        This tests that circular dependencies in one part of the task graph
        don't prevent independent tasks from being actionable.
        """
        plan = {
            "meta": {
                "project": "Partial Circular Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 3,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with partial circular deps",
                    "status": "in_progress",
                    "progress": {"completed": 0, "total": 3, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Task A (circular)",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.2"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Task B (circular)",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.3",
                            "title": "Task C (independent)",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],  # No dependencies - should be actionable
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # The independent task should still be actionable
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is not None, "Independent task should be actionable"
        _phase, task = next_task
        assert task["id"] == "0.1.3", "Independent task should be the next actionable task"


class TestNonExistentDependencies:
    """Tests for handling references to non-existent tasks."""

    def test_dependency_on_non_existent_task(self, tmp_plan_path):
        """Test task depending on a non-existent task ID.

        This tests that tasks with dependencies on non-existent tasks
        are not considered actionable.
        """
        plan = {
            "meta": {
                "project": "Non-existent Dep Test",
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
                    "name": "Test Phase",
                    "description": "Phase with non-existent dependency",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Task with bad dependency",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["9.9.9"],  # Non-existent task
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # Task with non-existent dependency should not be actionable
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is None, "Task with non-existent dependency should not be actionable"

    def test_multiple_dependencies_one_non_existent(self, tmp_plan_path):
        """Test task with multiple dependencies where one is non-existent.

        Even if some dependencies are valid, if any dependency is non-existent
        the task should not be actionable.
        """
        plan = {
            "meta": {
                "project": "Mixed Deps Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 2,
                "completed_tasks": 1,
                "overall_progress": 50,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with mixed dependencies",
                    "status": "in_progress",
                    "progress": {"completed": 1, "total": 2, "percentage": 50},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Completed Task",
                            "status": "completed",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {"completed_at": "2025-01-01T12:00:00Z"},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Task with mixed deps",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1", "9.9.9"],  # One valid, one invalid
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # Task should not be actionable due to non-existent dependency
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is None, "Task with any non-existent dependency should not be actionable"

    def test_dependency_on_future_task_cross_phase(self, tmp_plan_path):
        """Test task depending on a task in a different phase.

        This is valid and should work correctly - tests that cross-phase
        dependencies are properly handled.
        """
        plan = {
            "meta": {
                "project": "Cross-phase Dep Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 2,
                "total_tasks": 2,
                "completed_tasks": 1,
                "overall_progress": 50,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Phase 1",
                    "description": "First phase",
                    "status": "completed",
                    "progress": {"completed": 1, "total": 1, "percentage": 100},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Phase 1 Task",
                            "status": "completed",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {"completed_at": "2025-01-01T12:00:00Z"},
                        },
                    ],
                },
                {
                    "id": "1",
                    "name": "Phase 2",
                    "description": "Second phase",
                    "status": "in_progress",
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                    "tasks": [
                        {
                            "id": "1.1.1",
                            "title": "Phase 2 Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],  # Depends on task from phase 1
                            "tracking": {},
                        },
                    ],
                },
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # Cross-phase dependency should work if the dependency is completed
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is not None, "Task with completed cross-phase dependency should be actionable"
        _phase, task = next_task
        assert task["id"] == "1.1.1"


class TestValidDependencyChains:
    """Tests for valid dependency chains as control cases."""

    def test_simple_linear_dependency_chain(self, tmp_plan_path):
        """Test valid linear dependency chain: A -> B -> C.

        This is a control test showing that valid dependency chains
        work correctly without any circular issues.
        """
        plan = {
            "meta": {
                "project": "Linear Chain Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 3,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with linear dependencies",
                    "status": "in_progress",
                    "progress": {"completed": 0, "total": 3, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Task A",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],  # No dependencies - should be actionable
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Task B",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],  # Depends on A
                            "tracking": {},
                        },
                        {
                            "id": "0.1.3",
                            "title": "Task C",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.2"],  # Depends on B
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # First task with no dependencies should be actionable
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is not None
        _phase, task = next_task
        assert task["id"] == "0.1.1", "First task in linear chain should be actionable"

    def test_diamond_dependency_pattern(self, tmp_plan_path):
        """Test valid diamond dependency pattern: A -> B,C -> D.

        This tests a more complex but valid dependency structure where
        multiple tasks depend on one task, and one task depends on multiple tasks.
        """
        plan = {
            "meta": {
                "project": "Diamond Pattern Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 4,
                "completed_tasks": 1,
                "overall_progress": 25,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with diamond pattern",
                    "status": "in_progress",
                    "progress": {"completed": 1, "total": 4, "percentage": 25},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Task A (root)",
                            "status": "completed",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {"completed_at": "2025-01-01T12:00:00Z"},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Task B",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.3",
                            "title": "Task C",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.4",
                            "title": "Task D (converge)",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.2", "0.1.3"],  # Depends on both B and C
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # Either B or C should be actionable (both depend on completed A)
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is not None
        _phase, task = next_task
        assert task["id"] in ["0.1.2", "0.1.3"], "Tasks B or C should be actionable"

    def test_parallel_independent_tasks(self, tmp_plan_path):
        """Test multiple independent tasks with no dependencies.

        This control test verifies that multiple tasks without dependencies
        can all be considered actionable.
        """
        plan = {
            "meta": {
                "project": "Parallel Tasks Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 3,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with parallel tasks",
                    "status": "in_progress",
                    "progress": {"completed": 0, "total": 3, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Independent Task A",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Independent Task B",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.3",
                            "title": "Independent Task C",
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

        loaded_plan = cli.load_plan(tmp_plan_path)
        assert loaded_plan is not None

        # Should find one of the independent tasks
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is not None
        _phase, task = next_task
        assert task["id"] in ["0.1.1", "0.1.2", "0.1.3"]

    def test_dependency_progression_as_tasks_complete(self, tmp_plan_path, capsys):
        """Test that get_next_task progresses correctly as dependencies are met.

        This integration test verifies that as tasks are completed, their
        dependent tasks become actionable in the correct order.
        """
        plan = {
            "meta": {
                "project": "Progressive Deps Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 3,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with progressive dependencies",
                    "status": "in_progress",
                    "progress": {"completed": 0, "total": 3, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "First Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Second Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.3",
                            "title": "Third Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.2"],
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        # Step 1: First task should be actionable
        plan = cli.load_plan(tmp_plan_path)
        next_task = cli.get_next_task(plan)
        assert next_task is not None
        _phase, task = next_task
        assert task["id"] == "0.1.1"

        # Step 2: Complete first task, second should become actionable
        args = Namespace(file=tmp_plan_path, id="0.1.1", quiet=True)
        cli.cmd_done(args)

        plan = cli.load_plan(tmp_plan_path)
        next_task = cli.get_next_task(plan)
        assert next_task is not None
        _phase, task = next_task
        assert task["id"] == "0.1.2"

        # Step 3: Complete second task, third should become actionable
        args = Namespace(file=tmp_plan_path, id="0.1.2", quiet=True)
        cli.cmd_done(args)

        plan = cli.load_plan(tmp_plan_path)
        next_task = cli.get_next_task(plan)
        assert next_task is not None
        _phase, task = next_task
        assert task["id"] == "0.1.3"


class TestDependencyEdgeCases:
    """Tests for edge cases in dependency handling."""

    def test_empty_depends_on_array(self, tmp_plan_path):
        """Test task with empty depends_on array is actionable.

        An empty dependency array should be treated the same as no dependencies.
        """
        plan = {
            "meta": {
                "project": "Empty Deps Test",
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
                    "name": "Test Phase",
                    "description": "Phase with empty dependency array",
                    "status": "in_progress",
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Task with empty deps",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],  # Explicitly empty
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is not None
        _phase, task = next_task
        assert task["id"] == "0.1.1"

    def test_dependency_on_completed_task(self, tmp_plan_path):
        """Test task depending on completed task is actionable.

        This is the normal case - dependencies that are already completed
        should not block a task.
        """
        plan = {
            "meta": {
                "project": "Completed Dep Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 2,
                "completed_tasks": 1,
                "overall_progress": 50,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with completed dependency",
                    "status": "in_progress",
                    "progress": {"completed": 1, "total": 2, "percentage": 50},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Completed Task",
                            "status": "completed",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {"completed_at": "2025-01-01T12:00:00Z"},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Dependent Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is not None
        _phase, task = next_task
        assert task["id"] == "0.1.2"

    def test_dependency_on_pending_task_blocks(self, tmp_plan_path):
        """Test task depending on pending task is not actionable.

        A task should not be actionable if it depends on a pending task.
        """
        plan = {
            "meta": {
                "project": "Pending Dep Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 2,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with pending dependency",
                    "status": "in_progress",
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Pending Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Blocked Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is not None
        _phase, task = next_task
        # Should get the first pending task (0.1.1), not the blocked one (0.1.2)
        assert task["id"] == "0.1.1"

    def test_dependency_on_in_progress_task_blocks(self, tmp_plan_path):
        """Test task depending on in_progress task is not actionable.

        A task should wait until its dependencies are completed, not just started.
        """
        plan = {
            "meta": {
                "project": "In Progress Dep Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 1,
                "total_tasks": 2,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Phase with in_progress dependency",
                    "status": "in_progress",
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "In Progress Task",
                            "status": "in_progress",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {"started_at": "2025-01-01T12:00:00Z"},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Waiting Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": ["0.1.1"],
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan, indent=2))

        loaded_plan = cli.load_plan(tmp_plan_path)
        next_task = cli.get_next_task(loaded_plan)
        assert next_task is not None
        _phase, task = next_task
        # Should get the in_progress task, not the waiting one
        assert task["id"] == "0.1.1"
        assert task["status"] == "in_progress"
