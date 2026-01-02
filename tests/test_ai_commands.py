"""Tests for AI-optimized output commands."""

import json
import subprocess
import tempfile
from pathlib import Path


class TestAICommands:
    """Tests for --ai flag and files command."""

    def test_ai_context_basic(self, sample_plan_v2, tmp_path):
        """Test --ai flag produces compact output."""
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(sample_plan_v2))

        result = subprocess.run(
            ["pv", "-f", str(plan_file), "--ai"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Check for compact format
        assert "PROGRESS:" in result.stdout
        assert "PHASE:" in result.stdout or "NEXT:" in result.stdout

    def test_ai_actionable(self, sample_plan_v2, tmp_path):
        """Test --ai actionable shows only actionable tasks."""
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(sample_plan_v2))

        result = subprocess.run(
            ["pv", "-f", str(plan_file), "--ai", "actionable"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Output should be compact task lines or "none"
        output = result.stdout.strip()
        assert output  # Should have some output

    def test_files_command_no_files(self, sample_plan_v2, tmp_path):
        """Test files command when task has no files."""
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(sample_plan_v2))

        result = subprocess.run(
            ["pv", "-f", str(plan_file), "files"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "none"

    def test_files_command_with_files(self, tmp_path):
        """Test files command when task has files."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {"total_phases": 1, "total_tasks": 1, "completed_tasks": 0, "overall_progress": 0},
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Test task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "files": ["src/main.py:10-20", "src/utils.py:5"],
                            "tracking": {},
                        }
                    ],
                }
            ],
        }
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(plan))

        result = subprocess.run(
            ["pv", "-f", str(plan_file), "files"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "src/main.py:10-20" in result.stdout
        assert "src/utils.py:5" in result.stdout

    def test_files_command_specific_task(self, tmp_path):
        """Test files command with specific task ID."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {"total_phases": 1, "total_tasks": 2, "completed_tasks": 0, "overall_progress": 0},
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "First task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "files": ["first.py"],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Second task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "files": ["second.py"],
                            "tracking": {},
                        },
                    ],
                }
            ],
        }
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(plan))

        result = subprocess.run(
            ["pv", "-f", str(plan_file), "files", "0.1.2"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "second.py" in result.stdout
        assert "first.py" not in result.stdout


class TestSetNewFields:
    """Tests for setting new fields (files, research, plan)."""

    def test_set_files(self, sample_plan_v2, tmp_path):
        """Test setting files field."""
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(sample_plan_v2))

        # Find a task ID from the plan
        task_id = sample_plan_v2["phases"][0]["tasks"][0]["id"]

        result = subprocess.run(
            ["pv", "-f", str(plan_file), "set", task_id, "files", "src/main.py:10,src/utils.py"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Verify the file was updated
        updated = json.loads(plan_file.read_text())
        task = updated["phases"][0]["tasks"][0]
        assert task.get("files") == ["src/main.py:10", "src/utils.py"]

    def test_set_research(self, sample_plan_v2, tmp_path):
        """Test setting research field."""
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(sample_plan_v2))

        task_id = sample_plan_v2["phases"][0]["tasks"][0]["id"]

        result = subprocess.run(
            ["pv", "-f", str(plan_file), "set", task_id, "research", "Found pattern in src/auth.py:25"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        updated = json.loads(plan_file.read_text())
        task = updated["phases"][0]["tasks"][0]
        assert task.get("research") == "Found pattern in src/auth.py:25"

    def test_set_plan(self, sample_plan_v2, tmp_path):
        """Test setting plan field."""
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(sample_plan_v2))

        task_id = sample_plan_v2["phases"][0]["tasks"][0]["id"]

        result = subprocess.run(
            ["pv", "-f", str(plan_file), "set", task_id, "plan", "1. Add function\n2. Test it"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        updated = json.loads(plan_file.read_text())
        task = updated["phases"][0]["tasks"][0]
        assert task.get("plan") == "1. Add function\n2. Test it"

    def test_set_files_none(self, tmp_path):
        """Test clearing files field with 'none'."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {"total_phases": 1, "total_tasks": 1, "completed_tasks": 0, "overall_progress": 0},
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Test task",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "files": ["existing.py"],
                            "tracking": {},
                        }
                    ],
                }
            ],
        }
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(plan))

        result = subprocess.run(
            ["pv", "-f", str(plan_file), "set", "0.1.1", "files", "none"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        updated = json.loads(plan_file.read_text())
        task = updated["phases"][0]["tasks"][0]
        assert task.get("files") == []


class TestAddTaskWithFiles:
    """Tests for add-task with --files flag."""

    def test_add_task_with_files(self, sample_plan_v2, tmp_path):
        """Test adding task with files."""
        plan_file = tmp_path / "plan.json"
        plan_file.write_text(json.dumps(sample_plan_v2))

        phase_id = sample_plan_v2["phases"][0]["id"]

        result = subprocess.run(
            [
                "pv",
                "-f",
                str(plan_file),
                "add-task",
                phase_id,
                "New task with files",
                "--files",
                "src/new.py:1-10,src/helper.py",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        updated = json.loads(plan_file.read_text())
        # Find the new task
        new_task = None
        for task in updated["phases"][0]["tasks"]:
            if task["title"] == "New task with files":
                new_task = task
                break

        assert new_task is not None
        assert new_task.get("files") == ["src/new.py:1-10", "src/helper.py"]
