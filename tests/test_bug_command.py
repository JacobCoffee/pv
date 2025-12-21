"""Tests for the bug command."""

import json
import sys
from argparse import Namespace

import pytest

from plan_view import cli


class TestBugCommand:
    """Tests for bug command functionality."""

    def test_quiet_bug(self, sample_plan_file, capsys):
        """Test --quiet suppresses bug output."""
        args = Namespace(file=sample_plan_file, id="1.1.1", quiet=True)
        cli.cmd_bug(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_dry_run_bug(self, sample_plan_file, capsys):
        """Test --dry-run for bug doesn't save."""
        args = Namespace(file=sample_plan_file, id="0.1.1", quiet=False, dry_run=True)
        cli.cmd_bug(args)
        captured = capsys.readouterr()
        assert "Would:" in captured.out
        # Task should still be in original phase
        plan = cli.load_plan(sample_plan_file)
        result = cli.find_task(plan, "0.1.1")
        assert result is not None

    def test_cmd_bug(self, sample_plan_file, capsys):
        """Test bug command moves task to bugs phase."""
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_bug(args)
        captured = capsys.readouterr()
        assert "bug" in captured.out
        plan = json.loads(sample_plan_file.read_text())
        # Task should be removed from original phase
        assert len(plan["phases"][1]["tasks"]) == 1
        # Bugs phase should exist with the task
        bugs = next(p for p in plan["phases"] if p["id"] == "99")
        assert len(bugs["tasks"]) == 1
        assert bugs["tasks"][0]["title"] == "Feature X"
        assert bugs["tasks"][0]["id"] == "99.1.1"

    def test_cmd_bug_phase_structure(self, sample_plan_file, capsys):
        """Test bugs phase has correct structure."""
        plan = json.loads(sample_plan_file.read_text())
        # Bugs phase should exist by default
        bugs = next(p for p in plan["phases"] if p["id"] == "99")
        assert bugs["name"] == "Bugs"
        assert bugs["description"] == "Tasks identified as bugs requiring fixes"
        assert bugs["status"] == "pending"
        assert bugs["tasks"] == []

    def test_cmd_bug_uses_existing_phase(self, sample_plan_file, capsys):
        """Test bug reuses existing bugs phase and increments ID."""
        # Move first task to bugs
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_bug(args)
        # Move second task to bugs
        args = Namespace(file=sample_plan_file, id="1.1.2")
        cli.cmd_bug(args)
        plan = json.loads(sample_plan_file.read_text())
        bugs = next(p for p in plan["phases"] if p["id"] == "99")
        assert len(bugs["tasks"]) == 2
        # Second task should have incremented ID
        assert bugs["tasks"][1]["id"] == "99.1.2"

    def test_cmd_bug_handles_malformed_ids(self, tmp_plan_path, capsys):
        """Test bug handles existing tasks with malformed IDs."""
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
                            "id": "0.1.1",
                            "title": "Task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                    ],
                },
                {
                    "id": "99",
                    "name": "Bugs",
                    "description": "Bugs",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                    "tasks": [
                        {
                            "id": "short",
                            "title": "Short ID",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "99.x.y",
                            "title": "Non-numeric",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                    ],
                },
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan))
        args = Namespace(file=tmp_plan_path, id="0.1.1")
        cli.cmd_bug(args)
        result = json.loads(tmp_plan_path.read_text())
        bugs = next(p for p in result["phases"] if p["id"] == "99")
        # Should still work, defaulting to 1 for the new task
        assert bugs["tasks"][2]["id"] == "99.1.1"

    def test_cmd_bug_creates_new_task_when_not_found(self, sample_plan_file, capsys):
        """Test bug with non-existent task creates a new bug task."""
        args = Namespace(file=sample_plan_file, id="Fix login validation bug")
        cli.cmd_bug(args)
        captured = capsys.readouterr()
        assert "Added" in captured.out
        assert "Fix login validation bug" in captured.out

        # Verify task was created in bugs phase
        plan = json.loads(sample_plan_file.read_text())
        bugs = next(p for p in plan["phases"] if p["id"] == "99")
        new_task = next(t for t in bugs["tasks"] if t["title"] == "Fix login validation bug")
        assert new_task["status"] == "pending"

    def test_cmd_bug_file_not_found(self, tmp_path, capsys):
        """Test bug with non-existent file fails."""
        args = Namespace(file=tmp_path / "nonexistent.json", id="0.1.1")
        with pytest.raises(SystemExit):
            cli.cmd_bug(args)

    def test_cmd_bug_preserves_task_details(self, sample_plan_file, capsys):
        """Test bug command preserves all task details during move."""
        # Get original task details
        plan = cli.load_plan(sample_plan_file)
        result = cli.find_task(plan, "1.1.1")
        assert result is not None
        _, original_task = result
        original_title = original_task["title"]
        original_status = original_task["status"]
        original_agent = original_task.get("agent_type")
        original_depends = original_task.get("depends_on", [])

        # Move to bugs
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_bug(args)

        # Verify task details preserved
        plan = json.loads(sample_plan_file.read_text())
        bugs = next(p for p in plan["phases"] if p["id"] == "99")
        moved_task = bugs["tasks"][0]
        assert moved_task["title"] == original_title
        assert moved_task["status"] == original_status
        assert moved_task.get("agent_type") == original_agent
        assert moved_task.get("depends_on", []) == original_depends

    def test_main_bug(self, sample_plan_file, capsys, monkeypatch):
        """Test bug command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "bug", "1.1.1"])
        cli.main()
        captured = capsys.readouterr()
        assert "bug" in captured.out

    def test_main_bug_with_quiet(self, sample_plan_file, capsys, monkeypatch):
        """Test bug command via CLI with --quiet flag."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "bug", "1.1.1", "-q"])
        cli.main()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_main_bug_with_dry_run(self, sample_plan_file, capsys, monkeypatch):
        """Test bug command via CLI with --dry-run flag."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "bug", "1.1.1", "-d"])
        cli.main()
        captured = capsys.readouterr()
        assert "Would:" in captured.out
