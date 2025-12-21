"""Tests for the compact command."""

import json
import os
import sys
from argparse import Namespace
from pathlib import Path

from plan_view import cli
from plan_view.commands.edit import _compact_task, _rotate_backups


class TestCompactTask:
    """Tests for _compact_task helper."""

    def test_compact_completed_task_removes_extra_fields(self):
        """Test that extra fields are removed from completed tasks."""
        task = {
            "id": "0.1.1",
            "title": "Test Task",
            "status": "completed",
            "agent_type": "python-engineer",
            "depends_on": ["0.1.0"],
            "priority": "high",
            "tracking": {
                "started_at": "2025-01-01T00:00:00Z",
                "completed_at": "2025-01-02T00:00:00Z",
                "notes": "Done",
            },
        }
        modified = _compact_task(task)
        assert modified is True
        assert set(task.keys()) == {"id", "title", "status", "tracking"}
        assert task["tracking"] == {"completed_at": "2025-01-02T00:00:00Z"}

    def test_compact_already_minimal_task(self):
        """Test that already minimal task returns False."""
        task = {
            "id": "0.1.1",
            "title": "Test Task",
            "status": "completed",
            "tracking": {"completed_at": "2025-01-02T00:00:00Z"},
        }
        modified = _compact_task(task)
        assert modified is False

    def test_compact_task_empty_tracking(self):
        """Test compacting task with empty tracking."""
        task = {
            "id": "0.1.1",
            "title": "Test Task",
            "status": "completed",
            "agent_type": "test",
            "depends_on": [],
            "tracking": {},
        }
        modified = _compact_task(task)
        assert modified is True
        assert task["tracking"] == {}


class TestRotateBackups:
    """Tests for _rotate_backups helper."""

    def test_rotate_single_backup(self, tmp_path):
        """Test rotating when only one backup exists."""
        backup_dir = tmp_path / ".claude" / "plan-view"
        backup_dir.mkdir(parents=True)
        (backup_dir / "plan.json.1").write_text("{}")

        _rotate_backups(backup_dir, "plan", max_backups=5)

        assert not (backup_dir / "plan.json.1").exists()
        assert (backup_dir / "plan.json.2").exists()

    def test_rotate_multiple_backups(self, tmp_path):
        """Test rotating multiple backups."""
        backup_dir = tmp_path / ".claude" / "plan-view"
        backup_dir.mkdir(parents=True)
        for i in range(1, 4):
            (backup_dir / f"plan.json.{i}").write_text(f"backup{i}")

        _rotate_backups(backup_dir, "plan", max_backups=5)

        assert not (backup_dir / "plan.json.1").exists()
        assert (backup_dir / "plan.json.2").read_text() == "backup1"
        assert (backup_dir / "plan.json.3").read_text() == "backup2"
        assert (backup_dir / "plan.json.4").read_text() == "backup3"

    def test_rotate_deletes_oldest_at_max(self, tmp_path):
        """Test that oldest backup is deleted when at max."""
        backup_dir = tmp_path / ".claude" / "plan-view"
        backup_dir.mkdir(parents=True)
        for i in range(1, 6):
            (backup_dir / f"plan.json.{i}").write_text(f"backup{i}")

        _rotate_backups(backup_dir, "plan", max_backups=5)

        # .5 should be deleted, others rotated
        assert not (backup_dir / "plan.json.1").exists()
        assert not (backup_dir / "plan.json.6").exists()
        assert (backup_dir / "plan.json.5").read_text() == "backup4"

    def test_rotate_no_existing_backups(self, tmp_path):
        """Test rotation with no existing backups."""
        backup_dir = tmp_path / ".claude" / "plan-view"
        backup_dir.mkdir(parents=True)

        # Should not raise
        _rotate_backups(backup_dir, "plan", max_backups=5)


class TestCompactCommand:
    """Tests for cmd_compact command."""

    def test_compact_creates_backup(self, sample_plan_file, capsys):
        """Test that compact creates a backup file."""
        original_dir = Path.cwd()
        try:
            os.chdir(sample_plan_file.parent)
            args = Namespace(file=Path("plan.json"), max_backups=5, quiet=False, dry_run=False)
            # Rename sample_plan_file to plan.json in its directory
            plan_path = sample_plan_file.parent / "plan.json"
            sample_plan_file.rename(plan_path)
            args.file = plan_path

            cli.cmd_compact(args)

            backup_path = Path(".claude/plan-view/plan.json.1")
            assert backup_path.exists()
            captured = capsys.readouterr()
            assert "Backed up" in captured.out
        finally:
            os.chdir(original_dir)

    def test_compact_strips_completed_tasks(self, tmp_path, capsys):
        """Test that compact strips completed tasks to minimal fields."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {"total_phases": 1, "total_tasks": 2, "completed_tasks": 1, "overall_progress": 50},
            "phases": [
                {
                    "id": "0",
                    "name": "Test Phase",
                    "description": "Test",
                    "status": "in_progress",
                    "progress": {"completed": 1, "total": 2, "percentage": 50},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Completed Task",
                            "status": "completed",
                            "agent_type": "python-engineer",
                            "depends_on": [],
                            "priority": "high",
                            "tracking": {
                                "started_at": "2025-01-01T00:00:00Z",
                                "completed_at": "2025-01-02T00:00:00Z",
                            },
                        },
                        {
                            "id": "0.1.2",
                            "title": "Pending Task",
                            "status": "pending",
                            "agent_type": "ui-engineer",
                            "depends_on": ["0.1.1"],
                            "tracking": {},
                        },
                    ],
                },
                {
                    "id": "deferred",
                    "name": "Deferred",
                    "description": "Deferred tasks",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
                {
                    "id": "99",
                    "name": "Bugs",
                    "description": "Bug tasks",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
            ],
        }
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            args = Namespace(file=plan_path, max_backups=5, quiet=False, dry_run=False)
            cli.cmd_compact(args)

            # Check the plan was compacted
            compacted_plan = json.loads(plan_path.read_text())
            completed_task = compacted_plan["phases"][0]["tasks"][0]
            pending_task = compacted_plan["phases"][0]["tasks"][1]

            # Completed task should be minimal
            assert set(completed_task.keys()) == {"id", "title", "status", "tracking"}
            assert completed_task["tracking"] == {"completed_at": "2025-01-02T00:00:00Z"}

            # Pending task should be unchanged
            assert "agent_type" in pending_task
            assert "depends_on" in pending_task

            captured = capsys.readouterr()
            assert "Compacted 1 completed task" in captured.out
        finally:
            os.chdir(original_dir)

    def test_compact_dry_run(self, tmp_path, capsys):
        """Test that dry-run doesn't save changes."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {"total_phases": 1, "total_tasks": 1, "completed_tasks": 1, "overall_progress": 100},
            "phases": [
                {
                    "id": "0",
                    "name": "Test",
                    "description": "Test",
                    "status": "completed",
                    "progress": {"completed": 1, "total": 1, "percentage": 100},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Done",
                            "status": "completed",
                            "agent_type": "test",
                            "depends_on": [],
                            "tracking": {"completed_at": "2025-01-01T00:00:00Z"},
                        }
                    ],
                },
                {
                    "id": "deferred",
                    "name": "Deferred",
                    "description": "Deferred",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
                {
                    "id": "99",
                    "name": "Bugs",
                    "description": "Bugs",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
            ],
        }
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan))
        original_content = plan_path.read_text()

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            args = Namespace(file=plan_path, max_backups=5, quiet=False, dry_run=True)
            cli.cmd_compact(args)

            # Plan should be unchanged
            assert plan_path.read_text() == original_content

            captured = capsys.readouterr()
            assert "Would:" in captured.out
        finally:
            os.chdir(original_dir)

    def test_compact_quiet_mode(self, tmp_path, capsys):
        """Test that quiet mode suppresses output."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {"total_phases": 1, "total_tasks": 0, "completed_tasks": 0, "overall_progress": 0},
            "phases": [
                {
                    "id": "0",
                    "name": "Test",
                    "description": "Test",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
                {
                    "id": "deferred",
                    "name": "Deferred",
                    "description": "Deferred",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
                {
                    "id": "99",
                    "name": "Bugs",
                    "description": "Bugs",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
            ],
        }
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            args = Namespace(file=plan_path, max_backups=5, quiet=True, dry_run=False)
            cli.cmd_compact(args)

            captured = capsys.readouterr()
            assert captured.out == ""
        finally:
            os.chdir(original_dir)

    def test_compact_pluralization(self, tmp_path, capsys):
        """Test correct pluralization of 'task' vs 'tasks'."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {"total_phases": 1, "total_tasks": 2, "completed_tasks": 2, "overall_progress": 100},
            "phases": [
                {
                    "id": "0",
                    "name": "Test",
                    "description": "Test",
                    "status": "completed",
                    "progress": {"completed": 2, "total": 2, "percentage": 100},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Done 1",
                            "status": "completed",
                            "agent_type": "test",
                            "depends_on": [],
                            "tracking": {"completed_at": "2025-01-01T00:00:00Z"},
                        },
                        {
                            "id": "0.1.2",
                            "title": "Done 2",
                            "status": "completed",
                            "agent_type": "test",
                            "depends_on": [],
                            "tracking": {"completed_at": "2025-01-01T00:00:00Z"},
                        },
                    ],
                },
                {
                    "id": "deferred",
                    "name": "Deferred",
                    "description": "Deferred",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
                {
                    "id": "99",
                    "name": "Bugs",
                    "description": "Bugs",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
            ],
        }
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            args = Namespace(file=plan_path, max_backups=5, quiet=False, dry_run=False)
            cli.cmd_compact(args)

            captured = capsys.readouterr()
            assert "Compacted 2 completed tasks" in captured.out
        finally:
            os.chdir(original_dir)


class TestCompactCLI:
    """Test compact command via CLI main()."""

    def test_compact_via_main(self, tmp_path, monkeypatch, capsys):
        """Test compact command dispatches correctly via main()."""
        plan = {
            "meta": {
                "project": "Test",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {"total_phases": 1, "total_tasks": 1, "completed_tasks": 0, "overall_progress": 0},
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
                        }
                    ],
                },
                {
                    "id": "deferred",
                    "name": "Deferred",
                    "description": "Deferred",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
                {
                    "id": "99",
                    "name": "Bugs",
                    "description": "Bugs",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 0, "percentage": 0},
                    "tasks": [],
                },
            ],
        }
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            monkeypatch.setattr(sys, "argv", ["pv", "-f", str(plan_path), "compact", "-q"])
            cli.main()

            # Backup should exist
            backup_path = Path(".claude/plan-view/plan.json.1")
            assert backup_path.exists()
        finally:
            os.chdir(original_dir)
