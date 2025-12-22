"""Tests for the idea command."""

import json
import sys
from argparse import Namespace

import pytest

from plan_view import cli
from plan_view.commands.edit import cmd_idea


class TestIdeaCommand:
    """Tests for idea command functionality."""

    def test_quiet_idea(self, sample_plan_file, capsys):
        """Test --quiet suppresses idea output."""
        args = Namespace(file=sample_plan_file, id="1.1.1", quiet=True)
        cli.cmd_idea(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_dry_run_idea(self, sample_plan_file, capsys):
        """Test --dry-run for idea doesn't save."""
        args = Namespace(file=sample_plan_file, id="0.1.1", quiet=False, dry_run=True)
        cli.cmd_idea(args)
        captured = capsys.readouterr()
        assert "Would:" in captured.out
        # Task should still be in original phase
        plan = cli.load_plan(sample_plan_file)
        result = cli.find_task(plan, "0.1.1")
        assert result is not None

    def test_cmd_idea(self, sample_plan_file, capsys):
        """Test idea command moves task to ideas phase."""
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_idea(args)
        captured = capsys.readouterr()
        assert "idea" in captured.out
        plan = json.loads(sample_plan_file.read_text())
        # Task should be removed from original phase
        assert len(plan["phases"][1]["tasks"]) == 1
        # Ideas phase should exist with the task
        ideas = next(p for p in plan["phases"] if p["id"] == "ideas")
        assert len(ideas["tasks"]) == 1
        assert ideas["tasks"][0]["title"] == "Feature X"
        assert ideas["tasks"][0]["id"] == "ideas.1.1"

    def test_cmd_idea_phase_structure(self, sample_plan_file, capsys):
        """Test ideas phase has correct structure after creation."""
        # First create an idea to trigger phase creation
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_idea(args)

        plan = json.loads(sample_plan_file.read_text())
        ideas = next(p for p in plan["phases"] if p["id"] == "ideas")
        assert ideas["name"] == "Ideas"
        assert ideas["description"] == "Tasks stored as future ideas or concepts"
        assert ideas["status"] == "pending"
        assert len(ideas["tasks"]) == 1

    def test_cmd_idea_creates_phase_if_missing(self, tmp_plan_path, capsys):
        """Test idea creates ideas phase if called with plan missing it."""
        # Create a plan without the ideas phase (bypassing load_plan)
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {"total_phases": 0, "total_tasks": 0, "completed_tasks": 0, "overall_progress": 0},
            "phases": [],
        }
        tmp_plan_path.write_text(json.dumps(plan))

        # Call cmd_idea directly with the plan (simulating programmatic use)
        args = Namespace(file=tmp_plan_path, id="Test idea task")
        cmd_idea.__wrapped__(plan, args)

        # Phase should have been created
        ideas = next((p for p in plan["phases"] if p["id"] == "ideas"), None)
        assert ideas is not None
        assert ideas["name"] == "Ideas"
        assert len(ideas["tasks"]) == 1

    def test_cmd_idea_uses_existing_phase(self, sample_plan_file, capsys):
        """Test idea reuses existing ideas phase and increments ID."""
        # Move first task to ideas
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_idea(args)
        # Move second task to ideas
        args = Namespace(file=sample_plan_file, id="1.1.2")
        cli.cmd_idea(args)
        plan = json.loads(sample_plan_file.read_text())
        ideas = next(p for p in plan["phases"] if p["id"] == "ideas")
        assert len(ideas["tasks"]) == 2
        # Second task should have incremented ID
        assert ideas["tasks"][1]["id"] == "ideas.1.2"

    def test_cmd_idea_handles_malformed_ids(self, tmp_plan_path, capsys):
        """Test idea handles existing tasks with malformed IDs."""
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
                    "id": "ideas",
                    "name": "Ideas",
                    "description": "Ideas",
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
                            "id": "ideas.x.y",
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
        cli.cmd_idea(args)
        result = json.loads(tmp_plan_path.read_text())
        ideas = next(p for p in result["phases"] if p["id"] == "ideas")
        # Should still work, defaulting to 1 for the new task
        assert ideas["tasks"][2]["id"] == "ideas.1.1"

    def test_cmd_idea_creates_new_task_when_not_found(self, sample_plan_file, capsys):
        """Test idea with non-existent task creates a new idea task."""
        args = Namespace(file=sample_plan_file, id="Add dark mode toggle")
        cli.cmd_idea(args)
        captured = capsys.readouterr()
        assert "Added" in captured.out
        assert "Add dark mode toggle" in captured.out

        # Verify task was created in ideas phase
        plan = json.loads(sample_plan_file.read_text())
        ideas = next(p for p in plan["phases"] if p["id"] == "ideas")
        new_task = next(t for t in ideas["tasks"] if t["title"] == "Add dark mode toggle")
        assert new_task["status"] == "pending"

    def test_cmd_idea_new_task_dry_run(self, sample_plan_file, capsys):
        """Test idea dry-run for new task doesn't save."""
        original = sample_plan_file.read_text()
        args = Namespace(file=sample_plan_file, id="Dry run idea", dry_run=True, quiet=False)
        cli.cmd_idea(args)
        captured = capsys.readouterr()
        assert "Would:" in captured.out
        # File should be unchanged
        assert sample_plan_file.read_text() == original

    def test_cmd_idea_new_task_quiet(self, sample_plan_file, capsys):
        """Test idea quiet mode for new task suppresses output."""
        args = Namespace(file=sample_plan_file, id="Quiet idea", quiet=True)
        cli.cmd_idea(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_cmd_idea_file_not_found(self, tmp_path, capsys):
        """Test idea with non-existent file fails."""
        args = Namespace(file=tmp_path / "nonexistent.json", id="0.1.1")
        with pytest.raises(SystemExit):
            cli.cmd_idea(args)

    def test_cmd_idea_preserves_task_details(self, sample_plan_file, capsys):
        """Test idea command preserves all task details during move."""
        # Get original task details
        plan = cli.load_plan(sample_plan_file)
        result = cli.find_task(plan, "1.1.1")
        assert result is not None
        _, original_task = result
        original_title = original_task["title"]
        original_status = original_task["status"]
        original_agent = original_task.get("agent_type")
        original_depends = original_task.get("depends_on", [])

        # Move to ideas
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_idea(args)

        # Verify task details preserved
        plan = json.loads(sample_plan_file.read_text())
        ideas = next(p for p in plan["phases"] if p["id"] == "ideas")
        moved_task = ideas["tasks"][0]
        assert moved_task["title"] == original_title
        assert moved_task["status"] == original_status
        assert moved_task.get("agent_type") == original_agent
        assert moved_task.get("depends_on", []) == original_depends

    def test_main_idea(self, sample_plan_file, capsys, monkeypatch):
        """Test idea command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "idea", "1.1.1"])
        cli.main()
        captured = capsys.readouterr()
        assert "idea" in captured.out

    def test_main_idea_with_quiet(self, sample_plan_file, capsys, monkeypatch):
        """Test idea command via CLI with --quiet flag."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "idea", "1.1.1", "-q"])
        cli.main()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_main_idea_with_dry_run(self, sample_plan_file, capsys, monkeypatch):
        """Test idea command via CLI with --dry-run flag."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "idea", "1.1.1", "-d"])
        cli.main()
        captured = capsys.readouterr()
        assert "Would:" in captured.out


class TestIdeasViewCommand:
    """Tests for ideas view command functionality."""

    def test_cmd_ideas_empty(self, sample_plan_file, capsys):
        """Test ideas view with no ideas returns appropriate message."""
        cli.cmd_ideas(cli.load_plan(sample_plan_file), as_json=False)
        captured = capsys.readouterr()
        assert "No ideas phase found!" in captured.out

    def test_cmd_ideas_with_tasks(self, sample_plan_file, capsys):
        """Test ideas view shows tasks after adding ideas."""
        # Add an idea first
        args = Namespace(file=sample_plan_file, id="New feature idea")
        cli.cmd_idea(args)

        # View ideas
        plan = cli.load_plan(sample_plan_file)
        cli.cmd_ideas(plan, as_json=False)
        captured = capsys.readouterr()
        assert "Ideas" in captured.out
        assert "New feature idea" in captured.out

    def test_cmd_ideas_json(self, sample_plan_file, capsys):
        """Test ideas view with --json flag."""
        # Add an idea first (quiet to avoid polluting output)
        args = Namespace(file=sample_plan_file, id="JSON idea", quiet=True)
        cli.cmd_idea(args)

        # View ideas as JSON
        plan = cli.load_plan(sample_plan_file)
        cli.cmd_ideas(plan, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["id"] == "ideas"
        assert result["name"] == "Ideas"
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["title"] == "JSON idea"

    def test_cmd_ideas_json_empty(self, sample_plan_file, capsys):
        """Test ideas view --json with no ideas phase returns null."""
        plan = cli.load_plan(sample_plan_file)
        cli.cmd_ideas(plan, as_json=True)
        captured = capsys.readouterr()
        assert captured.out.strip() == "null"

    def test_main_ideas_view(self, sample_plan_file, capsys, monkeypatch):
        """Test ideas view command via CLI."""
        # Add an idea first
        args = Namespace(file=sample_plan_file, id="CLI view test")
        cli.cmd_idea(args)

        # View via CLI
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "ideas"])
        cli.main()
        captured = capsys.readouterr()
        assert "Ideas" in captured.out
        assert "CLI view test" in captured.out

    def test_main_ideas_view_alias(self, sample_plan_file, capsys, monkeypatch):
        """Test ideas view command via CLI with alias 'i'."""
        # Add an idea first
        args = Namespace(file=sample_plan_file, id="Alias test")
        cli.cmd_idea(args)

        # View via CLI with alias
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "i"])
        cli.main()
        captured = capsys.readouterr()
        assert "Ideas" in captured.out
        assert "Alias test" in captured.out

    def test_main_ideas_view_json(self, sample_plan_file, capsys, monkeypatch):
        """Test ideas view command via CLI with --json."""
        # Add an idea first (quiet to avoid polluting output)
        args = Namespace(file=sample_plan_file, id="JSON CLI test", quiet=True)
        cli.cmd_idea(args)

        # View via CLI with --json
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "ideas", "--json"])
        cli.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["id"] == "ideas"
        assert len(result["tasks"]) == 1
