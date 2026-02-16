"""Tests for the restore command."""

import json
import os
from argparse import Namespace
from pathlib import Path

import pytest

from plan_view.commands.edit import _list_restore_points, cmd_restore


def _make_plan(project="Test", updated_at="2025-01-01T00:00:00Z"):
    """Create a minimal valid plan for testing."""
    return {
        "meta": {
            "project": project,
            "version": "1.0.0",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": updated_at,
            "business_plan_path": ".claude/BUSINESS_PLAN.md",
        },
        "summary": {"total_phases": 1, "total_tasks": 0, "completed_tasks": 0, "overall_progress": 0},
        "phases": [
            {
                "id": "deferred",
                "name": "Deferred",
                "description": "Deferred",
                "status": "pending",
                "progress": {"completed": 0, "total": 0, "percentage": 0},
                "tasks": [],
            },
            {
                "id": "bugs",
                "name": "Bugs",
                "description": "Bugs",
                "status": "pending",
                "progress": {"completed": 0, "total": 0, "percentage": 0},
                "tasks": [],
            },
        ],
    }


def _setup_backups(tmp_path):
    """Create backup dir with sample restore points."""
    backup_dir = tmp_path / ".claude" / "plan-view"
    backup_dir.mkdir(parents=True)

    # Full backups
    old_plan = _make_plan(project="Old Project", updated_at="2025-01-01T00:00:00Z")
    (backup_dir / "plan.json.1").write_text(json.dumps(old_plan, indent=2))

    older_plan = _make_plan(project="Older Project", updated_at="2024-12-01T00:00:00Z")
    (backup_dir / "plan.json.2").write_text(json.dumps(older_plan, indent=2))

    # Delta backup
    delta = [{"op": "replace", "path": "/meta/project", "value": "Changed"}]
    (backup_dir / "plan.delta.1.json").write_text(json.dumps(delta, indent=2))

    return backup_dir


class TestListRestorePoints:
    """Tests for _list_restore_points."""

    def test_finds_full_backups(self, tmp_path):
        """Test that full backup files are discovered."""
        backup_dir = _setup_backups(tmp_path)
        points = _list_restore_points(backup_dir)

        full_points = [p for p in points if p["type"] == "full"]
        assert len(full_points) == 2

    def test_finds_delta_backups(self, tmp_path):
        """Test that delta backup files are discovered with operation count."""
        backup_dir = _setup_backups(tmp_path)
        points = _list_restore_points(backup_dir)

        delta_points = [p for p in points if p["type"] == "delta"]
        assert len(delta_points) == 1
        assert "1 operation" in delta_points[0]["label"]

    def test_sorted_newest_first(self, tmp_path):
        """Test that restore points are sorted by modification time, newest first."""
        backup_dir = _setup_backups(tmp_path)
        points = _list_restore_points(backup_dir)

        times = [p["modified"] for p in points]
        assert times == sorted(times, reverse=True)

    def test_empty_backup_dir(self, tmp_path):
        """Test that empty backup dir returns no points."""
        backup_dir = tmp_path / ".claude" / "plan-view"
        backup_dir.mkdir(parents=True)

        points = _list_restore_points(backup_dir)
        assert points == []

    def test_handles_corrupt_backup(self, tmp_path):
        """Test that corrupt backup files are still listed gracefully."""
        backup_dir = tmp_path / ".claude" / "plan-view"
        backup_dir.mkdir(parents=True)
        (backup_dir / "plan.json.1").write_text("not json{{{")

        points = _list_restore_points(backup_dir)
        assert len(points) == 1
        assert "Full backup #1" in points[0]["label"]


class TestRestoreList:
    """Tests for restore in list mode (no --point)."""

    def test_list_mode_shows_points(self, tmp_path, capsys):
        """Test that list mode displays available restore points."""
        _setup_backups(tmp_path)
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            args = Namespace(file=plan_path, point=None, quiet=False, dry_run=False)
            cmd_restore(args)

            captured = capsys.readouterr()
            assert "Available restore points:" in captured.out
            assert "full" in captured.out
            assert "delta" in captured.out
        finally:
            os.chdir(original_dir)

    def test_no_backup_dir_exits(self, tmp_path):
        """Test that missing backup dir causes exit."""
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            args = Namespace(file=plan_path, point=None, quiet=False, dry_run=False)
            with pytest.raises(SystemExit, match="1"):
                cmd_restore(args)
        finally:
            os.chdir(original_dir)

    def test_empty_backup_dir_exits(self, tmp_path):
        """Test that empty backup dir causes exit."""
        (tmp_path / ".claude" / "plan-view").mkdir(parents=True)
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            args = Namespace(file=plan_path, point=None, quiet=False, dry_run=False)
            with pytest.raises(SystemExit, match="1"):
                cmd_restore(args)
        finally:
            os.chdir(original_dir)


class TestRestoreExecution:
    """Tests for actually restoring a backup."""

    def test_restore_full_backup(self, tmp_path, capsys):
        """Test that restoring a full backup replaces the plan file."""
        _setup_backups(tmp_path)
        plan_path = tmp_path / "plan.json"
        current_plan = _make_plan(project="Current Project")
        plan_path.write_text(json.dumps(current_plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            points = _list_restore_points(tmp_path / ".claude" / "plan-view")
            full_idx = next(i for i, p in enumerate(points) if p["type"] == "full" and p["index"] == 1)

            args = Namespace(file=plan_path, point=str(full_idx + 1), quiet=False, dry_run=False)
            cmd_restore(args)

            restored = json.loads(plan_path.read_text())
            assert restored["meta"]["project"] == "Old Project"

            captured = capsys.readouterr()
            assert "Restored from:" in captured.out
        finally:
            os.chdir(original_dir)

    def test_restore_backs_up_current_first(self, tmp_path, capsys):
        """Test that current plan is backed up before restore overwrites it."""
        _setup_backups(tmp_path)
        plan_path = tmp_path / "plan.json"
        current_plan = _make_plan(project="Current Project")
        plan_path.write_text(json.dumps(current_plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            points = _list_restore_points(tmp_path / ".claude" / "plan-view")
            full_idx = next(i for i, p in enumerate(points) if p["type"] == "full" and p["index"] == 1)

            args = Namespace(file=plan_path, point=str(full_idx + 1), quiet=False, dry_run=False)
            cmd_restore(args)

            captured = capsys.readouterr()
            assert "Backed up current plan" in captured.out

            # The old plan.json.1 (Old Project) should now be at plan.json.2
            backup_dir = tmp_path / ".claude" / "plan-view"
            rotated = json.loads((backup_dir / "plan.json.2").read_text())
            assert rotated["meta"]["project"] == "Old Project"
        finally:
            os.chdir(original_dir)

    def test_restore_resets_periodic_counter(self, tmp_path, capsys):
        """Test that periodic.json is deleted after restore."""
        _setup_backups(tmp_path)
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        periodic_path = tmp_path / ".claude" / "plan-view" / "periodic.json"
        periodic_path.write_text(json.dumps({"count": 10, "base": _make_plan()}))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            points = _list_restore_points(tmp_path / ".claude" / "plan-view")
            full_idx = next(i for i, p in enumerate(points) if p["type"] == "full")

            args = Namespace(file=plan_path, point=str(full_idx + 1), quiet=True, dry_run=False)
            cmd_restore(args)

            assert not periodic_path.exists()
        finally:
            os.chdir(original_dir)

    def test_restore_delta_rejected(self, tmp_path):
        """Test that delta patches cannot be restored directly."""
        _setup_backups(tmp_path)
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            points = _list_restore_points(tmp_path / ".claude" / "plan-view")
            delta_idx = next(i for i, p in enumerate(points) if p["type"] == "delta")

            args = Namespace(file=plan_path, point=str(delta_idx + 1), quiet=False, dry_run=False)
            with pytest.raises(SystemExit, match="1"):
                cmd_restore(args)
        finally:
            os.chdir(original_dir)

    def test_restore_invalid_choice(self, tmp_path):
        """Test that out-of-range choice number exits with error."""
        _setup_backups(tmp_path)
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            args = Namespace(file=plan_path, point="999", quiet=False, dry_run=False)
            with pytest.raises(SystemExit, match="1"):
                cmd_restore(args)
        finally:
            os.chdir(original_dir)

    def test_restore_non_numeric_choice(self, tmp_path):
        """Test that non-numeric choice exits with error."""
        _setup_backups(tmp_path)
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            args = Namespace(file=plan_path, point="abc", quiet=False, dry_run=False)
            with pytest.raises(SystemExit, match="1"):
                cmd_restore(args)
        finally:
            os.chdir(original_dir)

    def test_restore_dry_run(self, tmp_path, capsys):
        """Test that dry-run mode does not modify the plan file."""
        _setup_backups(tmp_path)
        plan_path = tmp_path / "plan.json"
        current_plan = _make_plan(project="Current Project")
        plan_path.write_text(json.dumps(current_plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            points = _list_restore_points(tmp_path / ".claude" / "plan-view")
            full_idx = next(i for i, p in enumerate(points) if p["type"] == "full" and p["index"] == 1)

            args = Namespace(file=plan_path, point=str(full_idx + 1), quiet=False, dry_run=True)
            cmd_restore(args)

            unchanged = json.loads(plan_path.read_text())
            assert unchanged["meta"]["project"] == "Current Project"

            captured = capsys.readouterr()
            assert "Would:" in captured.out
        finally:
            os.chdir(original_dir)
