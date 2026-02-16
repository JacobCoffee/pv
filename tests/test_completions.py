"""Tests for shell tab completion."""

import json
from argparse import Namespace
from pathlib import Path

import pytest

from plan_view.completions import (
    _COMMANDS,
    AI_MODES,
    RM_TYPES,
    SET_FIELDS,
    cmd_complete,
    cmd_completion,
)
from plan_view.formatting import VALID_STATUSES


def _make_plan():
    """Create a minimal plan with tasks and phases."""
    return {
        "meta": {
            "project": "Test",
            "version": "1.0.0",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        },
        "phases": [
            {
                "id": "1",
                "name": "Phase One",
                "status": "in_progress",
                "progress": {"completed": 0, "total": 2, "percentage": 0},
                "tasks": [
                    {"id": "1.1", "title": "First task", "status": "pending"},
                    {"id": "1.2", "title": "Second task", "status": "in_progress"},
                ],
            },
            {
                "id": "2",
                "name": "Phase Two",
                "status": "pending",
                "progress": {"completed": 0, "total": 1, "percentage": 0},
                "tasks": [
                    {"id": "2.1", "title": "Third task", "status": "pending"},
                ],
            },
        ],
    }


@pytest.fixture
def plan_dir(tmp_path, monkeypatch):
    """Set up a temp dir with plan.json and chdir into it."""
    plan = _make_plan()
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=2))
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestCmdComplete:
    """Tests for the _complete hidden subcommand."""

    def test_task_ids(self, plan_dir, capsys):
        args = Namespace(file=Path("plan.json"), completion_type="task-ids")
        cmd_complete(args)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert "1.1" in lines
        assert "1.2" in lines
        assert "2.1" in lines

    def test_phase_ids(self, plan_dir, capsys):
        args = Namespace(file=Path("plan.json"), completion_type="phase-ids")
        cmd_complete(args)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert "1" in lines
        assert "2" in lines

    def test_missing_plan_no_crash(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = Namespace(file=Path("nonexistent.json"), completion_type="task-ids")
        cmd_complete(args)
        out = capsys.readouterr().out
        assert out.strip() == "" or out == ""

    def test_statuses(self, capsys):
        args = Namespace(file=Path("plan.json"), completion_type="statuses")
        cmd_complete(args)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        for s in VALID_STATUSES:
            assert s in lines

    def test_set_fields(self, capsys):
        args = Namespace(file=Path("plan.json"), completion_type="set-fields")
        cmd_complete(args)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        for f in SET_FIELDS:
            assert f in lines

    def test_rm_types(self, capsys):
        args = Namespace(file=Path("plan.json"), completion_type="rm-types")
        cmd_complete(args)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        for t in RM_TYPES:
            assert t in lines

    def test_ai_modes(self, capsys):
        args = Namespace(file=Path("plan.json"), completion_type="ai-modes")
        cmd_complete(args)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        for m in AI_MODES:
            assert m in lines

    def test_restore_points(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        backup_dir = tmp_path / ".claude" / "plan-view"
        backup_dir.mkdir(parents=True)
        plan = _make_plan()
        (backup_dir / "plan.json.1").write_text(json.dumps(plan))
        (backup_dir / "plan.json.2").write_text(json.dumps(plan))

        args = Namespace(file=Path("plan.json"), completion_type="restore-points")
        cmd_complete(args)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert "1" in lines
        assert "2" in lines

    def test_restore_points_no_backup_dir(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        args = Namespace(file=Path("plan.json"), completion_type="restore-points")
        cmd_complete(args)
        out = capsys.readouterr().out
        assert out.strip() == "" or out == ""


class TestCmdCompletion:
    """Tests for the completion shell script generator."""

    def test_bash_script(self, capsys):
        args = Namespace(shell="bash")
        cmd_completion(args)
        out = capsys.readouterr().out
        assert "_pv()" in out
        assert "complete -F _pv pv" in out
        assert "# Temporary:" in out
        assert "# Permanent:" in out

    def test_zsh_script(self, capsys):
        args = Namespace(shell="zsh")
        cmd_completion(args)
        out = capsys.readouterr().out
        assert "#compdef pv" in out
        assert "_pv" in out
        assert "# Temporary:" in out
        assert "# Permanent:" in out

    def test_fish_script(self, capsys):
        args = Namespace(shell="fish")
        cmd_completion(args)
        out = capsys.readouterr().out
        assert "complete -c pv" in out
        assert "# Temporary:" in out
        assert "# Permanent:" in out

    def test_all_commands_in_bash(self, capsys):
        args = Namespace(shell="bash")
        cmd_completion(args)
        out = capsys.readouterr().out
        for name, _alias, _desc in _COMMANDS:
            assert name in out

    def test_all_commands_in_zsh(self, capsys):
        args = Namespace(shell="zsh")
        cmd_completion(args)
        out = capsys.readouterr().out
        for name, _alias, _desc in _COMMANDS:
            assert name in out

    def test_all_commands_in_fish(self, capsys):
        args = Namespace(shell="fish")
        cmd_completion(args)
        out = capsys.readouterr().out
        for name, _alias, _desc in _COMMANDS:
            assert name in out

    def test_unknown_shell(self, capsys):
        args = Namespace(shell="powershell")
        with pytest.raises(SystemExit, match="1"):
            cmd_completion(args)
