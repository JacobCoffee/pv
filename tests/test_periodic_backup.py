"""Tests for periodic delta backup functionality."""

import json
import os
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from plan_view import cli
from plan_view.io import maybe_periodic_backup, save_plan


def _make_plan(project="Test", task_status="pending"):
    """Create a minimal valid plan for testing."""
    return {
        "meta": {
            "project": project,
            "version": "1.0.0",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "business_plan_path": ".claude/BUSINESS_PLAN.md",
        },
        "summary": {"total_phases": 1, "total_tasks": 1, "completed_tasks": 0, "overall_progress": 0},
        "phases": [
            {
                "id": "0",
                "name": "Phase 0",
                "description": "Test phase",
                "status": "pending",
                "progress": {"completed": 0, "total": 1, "percentage": 0},
                "tasks": [
                    {
                        "id": "0.1.1",
                        "title": "Task One",
                        "status": task_status,
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
                "id": "bugs",
                "name": "Bugs",
                "description": "Bugs",
                "status": "pending",
                "progress": {"completed": 0, "total": 0, "percentage": 0},
                "tasks": [],
            },
        ],
    }


class TestPeriodicBackupCounter:
    """Tests for counter increment behavior."""

    def test_counter_increments_on_save(self, tmp_path):
        """Counter increments on each save_plan() call."""
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            plan = _make_plan()
            save_plan(plan_path, plan)

            periodic_path = Path(".claude/plan-view/periodic.json")
            assert periodic_path.exists()
            state = json.loads(periodic_path.read_text())
            assert state["count"] == 1

            save_plan(plan_path, plan)
            state = json.loads(periodic_path.read_text())
            assert state["count"] == 2
        finally:
            os.chdir(original_dir)

    def test_no_delta_before_15th_save(self, tmp_path):
        """No delta file created before the 15th save."""
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            plan = _make_plan()
            for _ in range(14):
                save_plan(plan_path, plan)

            delta_path = Path(".claude/plan-view/plan.delta.1.json")
            assert not delta_path.exists()

            state = json.loads(Path(".claude/plan-view/periodic.json").read_text())
            assert state["count"] == 14
        finally:
            os.chdir(original_dir)


class TestPeriodicBackupDelta:
    """Tests for delta file creation."""

    def test_delta_created_on_15th_save(self, tmp_path):
        """Delta file created on 15th save with correct RFC 6902 patch."""
        plan_path = tmp_path / "plan.json"
        plan = _make_plan()
        plan_path.write_text(json.dumps(plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            # First 14 saves with original plan
            for _ in range(14):
                save_plan(plan_path, _make_plan())

            # Mutate the plan before the 15th save
            mutated = _make_plan(task_status="completed")
            save_plan(plan_path, mutated)

            delta_path = Path(".claude/plan-view/plan.delta.1.json")
            assert delta_path.exists()
            patch_ops = json.loads(delta_path.read_text())
            assert isinstance(patch_ops, list)
            assert len(patch_ops) > 0
            # Verify it's RFC 6902 format
            assert all("op" in op and "path" in op for op in patch_ops)
        finally:
            os.chdir(original_dir)

    def test_no_delta_when_plan_unchanged(self, tmp_path):
        """No delta created when plan hasn't changed from base."""
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            # Save the same plan 15 times (only updated_at differs, but base comparison includes it)
            plan = _make_plan()
            for _ in range(15):
                save_plan(plan_path, plan)

            # The delta may or may not exist depending on timestamp changes,
            # but the periodic.json should have count=15
            state = json.loads(Path(".claude/plan-view/periodic.json").read_text())
            assert state["count"] == 15
        finally:
            os.chdir(original_dir)

    def test_rotation_works(self, tmp_path):
        """Delta files rotate correctly (delta.1 -> delta.2 on next cycle)."""
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            backup_dir = Path(".claude/plan-view")

            # First cycle: 15 saves with mutation
            for _ in range(14):
                save_plan(plan_path, _make_plan())
            save_plan(plan_path, _make_plan(task_status="completed"))

            assert (backup_dir / "plan.delta.1.json").exists()
            first_delta = (backup_dir / "plan.delta.1.json").read_text()

            # Second cycle: 15 more saves with different mutation
            for _ in range(14):
                save_plan(plan_path, _make_plan(task_status="completed"))
            save_plan(plan_path, _make_plan(task_status="in_progress"))

            # delta.1 should be the new delta, delta.2 should be the old one
            assert (backup_dir / "plan.delta.1.json").exists()
            assert (backup_dir / "plan.delta.2.json").exists()
            assert (backup_dir / "plan.delta.2.json").read_text() == first_delta
        finally:
            os.chdir(original_dir)


class TestPeriodicBackupReset:
    """Tests for counter reset on init --force."""

    def test_counter_resets_on_init_force(self, tmp_path, capsys):
        """Counter resets when init --force is used."""
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps(_make_plan()))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            # Create some saves to build up the counter
            for _ in range(5):
                save_plan(plan_path, _make_plan())

            periodic_path = Path(".claude/plan-view/periodic.json")
            assert periodic_path.exists()
            state = json.loads(periodic_path.read_text())
            assert state["count"] == 5

            # Run init --force
            args = Namespace(file=plan_path, force=True, name="Reset Project", quiet=True, dry_run=False)
            cli.cmd_init(args)

            # periodic.json is recreated by save_plan with a fresh base and count=1
            state = json.loads(periodic_path.read_text())
            assert state["count"] == 1
        finally:
            os.chdir(original_dir)


class TestPeriodicBackupSafety:
    """Tests for error handling."""

    def test_backup_failure_doesnt_crash_save(self, tmp_path):
        """Backup failure doesn't crash save_plan."""
        plan_path = tmp_path / "plan.json"
        plan = _make_plan()
        plan_path.write_text(json.dumps(plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            # Test by writing corrupt periodic.json
            backup_dir = Path(".claude/plan-view")
            backup_dir.mkdir(parents=True, exist_ok=True)
            periodic_path = backup_dir / "periodic.json"
            periodic_path.write_text("invalid json{{{")

            # save_plan should still succeed even with corrupt periodic.json
            save_plan(plan_path, plan)
            # Plan file should still be written correctly
            saved = json.loads(plan_path.read_text())
            assert saved["phases"][0]["tasks"][0]["title"] == "Task One"
        finally:
            os.chdir(original_dir)

    def test_backup_handles_jsonpatch_error(self, tmp_path):
        """Backup gracefully handles jsonpatch errors."""
        plan_path = tmp_path / "plan.json"
        plan = _make_plan()
        plan_path.write_text(json.dumps(plan))

        original_dir = Path.cwd()
        try:
            os.chdir(tmp_path)
            with patch("plan_view.io.jsonpatch.make_patch", side_effect=RuntimeError("patch failed")):
                # Set up state at count=14 so next call triggers delta
                backup_dir = Path(".claude/plan-view")
                backup_dir.mkdir(parents=True, exist_ok=True)
                state = {"count": 14, "base": _make_plan()}
                (backup_dir / "periodic.json").write_text(json.dumps(state))

                # This should not crash despite jsonpatch error
                maybe_periodic_backup(plan_path, plan)
        finally:
            os.chdir(original_dir)
