"""Tests for future command functionality."""

import json
import sys
from argparse import Namespace

from plan_view import cli


class TestFutureCommand:
    """Tests for future command functionality."""

    def test_future_shows_pending_tasks(self, sample_plan_file, capsys):
        """Test future shows pending tasks."""
        plan = json.loads(sample_plan_file.read_text())
        cli.cmd_future(plan, as_json=False)
        captured = capsys.readouterr()

        assert "Upcoming Tasks:" in captured.out
        assert "1.1.1" in captured.out

    def test_future_json_output(self, sample_plan_file, capsys):
        """Test future JSON output format."""
        plan = json.loads(sample_plan_file.read_text())
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert isinstance(output, list)
        assert len(output) > 0
        assert "id" in output[0]
        assert "title" in output[0]
        assert "status" in output[0]
        assert "actionable" in output[0]

    def test_future_with_count(self, sample_plan_file, capsys):
        """Test future with count limit."""
        plan = json.loads(sample_plan_file.read_text())
        cli.cmd_future(plan, count=1, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert len(output) == 1

    def test_future_with_none_count_shows_all(self, sample_plan_file, capsys):
        """Test future with None count shows all tasks."""
        plan = json.loads(sample_plan_file.read_text())
        cli.cmd_future(plan, count=None, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert len(output) >= 2  # Sample has multiple pending tasks

    def test_future_no_pending_tasks(self, capsys):
        """Test future when no pending tasks exist."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Phase 1",
                    "description": "Test phase",
                    "status": "completed",
                    "tasks": [
                        {"id": "1.1.1", "title": "Done task", "status": "completed", "tracking": {}},
                    ],
                    "progress": {"completed": 1, "total": 1, "percentage": 100},
                }
            ]
        }
        cli.cmd_future(plan, as_json=False)
        captured = capsys.readouterr()

        assert "No upcoming tasks found!" in captured.out

    def test_future_no_pending_tasks_json(self, capsys):
        """Test future JSON output when no pending tasks."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Phase 1",
                    "description": "Test",
                    "status": "completed",
                    "tasks": [
                        {"id": "1.1.1", "title": "Done", "status": "completed", "tracking": {}},
                    ],
                    "progress": {"completed": 1, "total": 1, "percentage": 100},
                }
            ]
        }
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        assert captured.out.strip() == "[]"

    def test_future_skips_special_phases(self, sample_plan_file, capsys):
        """Test future skips deferred/bugs/ideas phases."""
        plan = json.loads(sample_plan_file.read_text())
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        phase_ids = [t["phase_id"] for t in output]
        assert "deferred" not in phase_ids
        assert "bugs" not in phase_ids
        assert "ideas" not in phase_ids

    def test_future_skips_completed_phases(self, capsys):
        """Test future skips completed phases."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Completed Phase",
                    "description": "Done",
                    "status": "completed",
                    "tasks": [
                        {"id": "1.1.1", "title": "Old pending", "status": "pending", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                },
                {
                    "id": "2",
                    "name": "Active Phase",
                    "description": "Current",
                    "status": "in_progress",
                    "tasks": [
                        {"id": "2.1.1", "title": "Current task", "status": "pending", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                },
            ]
        }
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert len(output) == 1
        assert output[0]["phase_id"] == "2"

    def test_future_shows_in_progress_first(self, capsys):
        """Test future shows in_progress tasks before pending."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Phase 1",
                    "description": "Test",
                    "status": "in_progress",
                    "tasks": [
                        {"id": "1.1.1", "title": "Pending task", "status": "pending", "tracking": {}},
                        {"id": "1.1.2", "title": "In progress task", "status": "in_progress", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                }
            ]
        }
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert output[0]["status"] == "in_progress"
        assert output[1]["status"] == "pending"

    def test_future_shows_actionable_before_waiting(self, capsys):
        """Test future shows actionable tasks before waiting on deps."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Phase 1",
                    "description": "Test",
                    "status": "in_progress",
                    "tasks": [
                        {
                            "id": "1.1.1",
                            "title": "Waiting task",
                            "status": "pending",
                            "depends_on": ["1.1.3"],
                            "tracking": {},
                        },
                        {"id": "1.1.2", "title": "Actionable task", "status": "pending", "tracking": {}},
                        {"id": "1.1.3", "title": "Blocker", "status": "pending", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 3, "percentage": 0},
                }
            ]
        }
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        # Actionable tasks (1.1.2, 1.1.3) should come before waiting task (1.1.1)
        actionable_tasks = [t for t in output if t["actionable"]]
        waiting_tasks = [t for t in output if not t["actionable"]]
        assert len(actionable_tasks) == 2
        assert len(waiting_tasks) == 1
        # All actionable tasks should appear before waiting tasks
        actionable_indices = [output.index(t) for t in actionable_tasks]
        waiting_indices = [output.index(t) for t in waiting_tasks]
        assert max(actionable_indices) < min(waiting_indices)

    def test_future_shows_blocked_last(self, capsys):
        """Test future shows blocked tasks last."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Phase 1",
                    "description": "Test",
                    "status": "in_progress",
                    "tasks": [
                        {"id": "1.1.1", "title": "Blocked task", "status": "blocked", "tracking": {}},
                        {"id": "1.1.2", "title": "Pending task", "status": "pending", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                }
            ]
        }
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert output[0]["status"] == "pending"
        assert output[1]["status"] == "blocked"

    def test_future_display_icons(self, capsys):
        """Test future displays correct icons for different states."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Phase 1",
                    "description": "Test",
                    "status": "in_progress",
                    "tasks": [
                        {"id": "1.1.1", "title": "In progress", "status": "in_progress", "tracking": {}},
                        {"id": "1.1.2", "title": "Blocked", "status": "blocked", "tracking": {}},
                        {"id": "1.1.3", "title": "Ready", "status": "pending", "tracking": {}},
                        {
                            "id": "1.1.4",
                            "title": "Waiting",
                            "status": "pending",
                            "depends_on": ["1.1.5"],
                            "tracking": {},
                        },
                        {"id": "1.1.5", "title": "Blocker", "status": "pending", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 5, "percentage": 0},
                }
            ]
        }
        cli.cmd_future(plan, as_json=False)
        captured = capsys.readouterr()

        # Check icons are present
        assert "\U0001f504" in captured.out  # in_progress icon
        assert "\U0001f6ab" in captured.out  # blocked icon
        assert "\U0001f449" in captured.out  # ready icon
        assert "\u23f3" in captured.out  # waiting icon

    def test_future_display_status_info(self, capsys):
        """Test future displays status info correctly."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Phase 1",
                    "description": "Test",
                    "status": "in_progress",
                    "tasks": [
                        {"id": "1.1.1", "title": "Ready task", "status": "pending", "tracking": {}},
                        {
                            "id": "1.1.2",
                            "title": "Waiting task",
                            "status": "pending",
                            "depends_on": ["1.1.3"],
                            "tracking": {},
                        },
                        {"id": "1.1.3", "title": "Blocker", "status": "pending", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 3, "percentage": 0},
                }
            ]
        }
        cli.cmd_future(plan, as_json=False)
        captured = capsys.readouterr()

        assert "ready" in captured.out
        assert "waiting" in captured.out

    def test_future_via_main_with_alias(self, sample_plan_file, capsys, monkeypatch):
        """Test future via CLI with 'f' alias."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["pv", "-f", str(sample_plan_file), "f"],
        )
        cli.main()
        captured = capsys.readouterr()

        assert "Upcoming Tasks:" in captured.out

    def test_future_via_main_with_count(self, sample_plan_file, capsys, monkeypatch):
        """Test future via CLI with -n count flag."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["pv", "-f", str(sample_plan_file), "future", "-n", "1"],
        )
        cli.main()
        captured = capsys.readouterr()

        # Should only show 1 task
        assert "Upcoming Tasks:" in captured.out

    def test_future_via_main_with_all_flag(self, sample_plan_file, capsys, monkeypatch):
        """Test future via CLI with -a all flag."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["pv", "-f", str(sample_plan_file), "future", "-a"],
        )
        cli.main()
        captured = capsys.readouterr()

        assert "Upcoming Tasks:" in captured.out

    def test_future_via_main_json(self, sample_plan_file, capsys, monkeypatch):
        """Test future via CLI with --json flag."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["pv", "-f", str(sample_plan_file), "future", "--json"],
        )
        cli.main()
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert isinstance(output, list)

    def test_future_includes_depends_on_in_json(self, capsys):
        """Test future JSON includes depends_on field."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Phase 1",
                    "description": "Test",
                    "status": "in_progress",
                    "tasks": [
                        {
                            "id": "1.1.1",
                            "title": "Task with deps",
                            "status": "pending",
                            "depends_on": ["1.1.2"],
                            "tracking": {},
                        },
                        {"id": "1.1.2", "title": "No deps", "status": "pending", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                }
            ]
        }
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        task_with_deps = next(t for t in output if t["id"] == "1.1.1")
        assert task_with_deps["depends_on"] == ["1.1.2"]

    def test_future_skips_skipped_phases(self, capsys):
        """Test future skips skipped phases."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Skipped Phase",
                    "description": "Skipped",
                    "status": "skipped",
                    "tasks": [
                        {"id": "1.1.1", "title": "Skipped task", "status": "pending", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                },
                {
                    "id": "2",
                    "name": "Active Phase",
                    "description": "Active",
                    "status": "in_progress",
                    "tasks": [
                        {"id": "2.1.1", "title": "Active task", "status": "pending", "tracking": {}},
                    ],
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                },
            ]
        }
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert len(output) == 1
        assert output[0]["phase_id"] == "2"

    def test_future_actionable_with_completed_deps(self, capsys):
        """Test future correctly marks tasks with completed deps as actionable."""
        plan = {
            "phases": [
                {
                    "id": "1",
                    "name": "Phase 1",
                    "description": "Test",
                    "status": "in_progress",
                    "tasks": [
                        {"id": "1.1.1", "title": "Completed task", "status": "completed", "tracking": {}},
                        {
                            "id": "1.1.2",
                            "title": "Depends on completed",
                            "status": "pending",
                            "depends_on": ["1.1.1"],
                            "tracking": {},
                        },
                    ],
                    "progress": {"completed": 1, "total": 2, "percentage": 50},
                }
            ]
        }
        cli.cmd_future(plan, as_json=True)
        captured = capsys.readouterr()

        output = json.loads(captured.out)
        assert len(output) == 1
        assert output[0]["id"] == "1.1.2"
        assert output[0]["actionable"] is True
