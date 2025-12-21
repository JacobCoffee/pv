"""Comprehensive tests for pv-tool CLI - targeting 100% coverage."""

import json
import sys
from argparse import Namespace
from datetime import datetime
from io import StringIO
from unittest.mock import patch

import pytest

from plan_view import cli

# ============ FORMATTING FUNCTIONS ============


class TestFormatting:
    """Tests for ANSI formatting helper functions."""

    def test_bold(self, monkeypatch):
        """Test bold formatting applies correct ANSI codes."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        result = cli.bold("test")
        assert result == "\033[1mtest\033[0m"

    def test_dim(self, monkeypatch):
        """Test dim formatting applies correct ANSI codes."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        result = cli.dim("test")
        assert result == "\033[2mtest\033[0m"

    def test_green(self, monkeypatch):
        """Test green formatting applies correct ANSI codes."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        result = cli.green("test")
        assert result == "\033[32mtest\033[0m"

    def test_bold_cyan(self, monkeypatch):
        """Test bold cyan formatting applies correct ANSI codes."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        result = cli.bold_cyan("test")
        assert result == "\033[1m\033[36mtest\033[0m"

    def test_bold_yellow(self, monkeypatch):
        """Test bold yellow formatting applies correct ANSI codes."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        result = cli.bold_yellow("test")
        assert result == "\033[1m\033[33mtest\033[0m"


class TestQuietFlag:
    """Tests for --quiet / -q flag on edit commands."""

    def test_quiet_done(self, sample_plan_file, capsys):
        """Test --quiet suppresses done output."""
        args = Namespace(file=sample_plan_file, id="0.1.2", quiet=True)
        cli.cmd_done(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_start(self, sample_plan_file, capsys):
        """Test --quiet suppresses start output."""
        args = Namespace(file=sample_plan_file, id="1.1.1", quiet=True)
        cli.cmd_start(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_block(self, sample_plan_file, capsys):
        """Test --quiet suppresses block output."""
        args = Namespace(file=sample_plan_file, id="1.1.1", quiet=True)
        cli.cmd_block(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_skip(self, sample_plan_file, capsys):
        """Test --quiet suppresses skip output."""
        args = Namespace(file=sample_plan_file, id="1.1.1", quiet=True)
        cli.cmd_skip(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_defer(self, sample_plan_file, capsys):
        """Test --quiet suppresses defer output."""
        args = Namespace(file=sample_plan_file, id="1.1.1", quiet=True)
        cli.cmd_defer(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_rm_task(self, sample_plan_file, capsys):
        """Test --quiet suppresses rm task output."""
        args = Namespace(file=sample_plan_file, type="task", id="0.1.1", quiet=True)
        cli.cmd_rm(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_rm_phase(self, sample_plan_file, capsys):
        """Test --quiet suppresses rm phase output."""
        args = Namespace(file=sample_plan_file, type="phase", id="1", quiet=True)
        cli.cmd_rm(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_init(self, tmp_path, capsys):
        """Test --quiet suppresses init output."""
        args = Namespace(file=tmp_path / "plan.json", name="Test", force=False, quiet=True)
        cli.cmd_init(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_add_phase(self, sample_plan_file, capsys):
        """Test --quiet suppresses add-phase output."""
        args = Namespace(file=sample_plan_file, name="New Phase", desc=None, quiet=True)
        cli.cmd_add_phase(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_add_task(self, sample_plan_file, capsys):
        """Test --quiet suppresses add-task output."""
        args = Namespace(file=sample_plan_file, phase="0", title="New Task", agent=None, deps=None, quiet=True)
        cli.cmd_add_task(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_set(self, sample_plan_file, capsys):
        """Test --quiet suppresses set output."""
        args = Namespace(file=sample_plan_file, id="0.1.1", field="title", value="New Title", quiet=True)
        cli.cmd_set(args)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_quiet_via_cli(self, sample_plan_file, capsys, monkeypatch):
        """Test -q flag via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "done", "0.1.2", "-q"])
        cli.main()
        captured = capsys.readouterr()
        assert captured.out == ""


class TestNoColor:
    """Tests for NO_COLOR environment variable support."""

    def test_no_color_disables_formatting(self, monkeypatch):
        """Test NO_COLOR env var disables all ANSI formatting."""
        monkeypatch.setenv("NO_COLOR", "1")
        assert cli.bold("test") == "test"
        assert cli.dim("test") == "test"
        assert cli.green("test") == "test"
        assert cli.bold_cyan("test") == "test"
        assert cli.bold_yellow("test") == "test"

    def test_no_color_any_value(self, monkeypatch):
        """Test NO_COLOR works with any value (per spec)."""
        monkeypatch.setenv("NO_COLOR", "")
        # Empty string is falsy, so colors should still work
        # Only truthy values disable color per the standard
        monkeypatch.setenv("FORCE_COLOR", "1")
        assert cli.bold("test") == "\033[1mtest\033[0m"

    def test_force_color_overrides_tty_check(self, monkeypatch):
        """Test FORCE_COLOR enables colors even when not a TTY."""
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.delenv("NO_COLOR", raising=False)
        # Even if stdout is not a TTY, FORCE_COLOR should enable colors
        assert cli.bold("test") == "\033[1mtest\033[0m"

    def test_no_color_takes_precedence(self, monkeypatch):
        """Test NO_COLOR takes precedence over FORCE_COLOR."""
        monkeypatch.setenv("NO_COLOR", "1")
        monkeypatch.setenv("FORCE_COLOR", "1")
        assert cli.bold("test") == "test"

    def test_pipe_disables_color(self, monkeypatch):
        """Test color is disabled when stdout is not a TTY."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("FORCE_COLOR", raising=False)
        with patch("sys.stdout.isatty", return_value=False):
            assert cli.bold("test") == "test"

    def test_tty_enables_color(self, monkeypatch):
        """Test color is enabled when stdout is a TTY."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("FORCE_COLOR", raising=False)
        with patch("sys.stdout.isatty", return_value=True):
            assert cli.bold("test") == "\033[1mtest\033[0m"


# ============ UTILITY FUNCTIONS ============


class TestUtilities:
    """Tests for utility functions."""

    def test_now_iso_format(self):
        """Test now_iso returns valid ISO 8601 format."""
        result = cli.now_iso()
        assert result.endswith("Z")
        assert "T" in result
        # Should be parseable

        datetime.fromisoformat(result)

    def test_get_status_icon_completed(self):
        """Test status icon for completed."""
        assert cli.get_status_icon("completed") == "\u2705"

    def test_get_status_icon_in_progress(self):
        """Test status icon for in_progress."""
        assert cli.get_status_icon("in_progress") == "\U0001f504"

    def test_get_status_icon_pending(self):
        """Test status icon for pending."""
        assert cli.get_status_icon("pending") == "\u23f3"

    def test_get_status_icon_blocked(self):
        """Test status icon for blocked."""
        assert cli.get_status_icon("blocked") == "\U0001f6d1"

    def test_get_status_icon_skipped(self):
        """Test status icon for skipped."""
        assert cli.get_status_icon("skipped") == "\u23ed\ufe0f"

    def test_get_status_icon_unknown(self):
        """Test status icon for unknown status returns question mark."""
        assert cli.get_status_icon("unknown") == "\u2753"


# ============ FILE I/O ============


class TestFileIO:
    """Tests for plan file loading and saving."""

    def test_load_plan_success(self, sample_plan_file, sample_plan):
        """Test loading a valid plan file."""
        result = cli.load_plan(sample_plan_file)
        assert result is not None
        assert result["meta"]["project"] == "Test Project"

    def test_load_plan_not_found(self, tmp_path, capsys):
        """Test loading a non-existent file."""
        path = tmp_path / "nonexistent.json"
        result = cli.load_plan(path)
        assert result is None
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_load_plan_invalid_json(self, tmp_plan_path, capsys):
        """Test loading a file with invalid JSON."""
        tmp_plan_path.write_text("{ invalid json }")
        result = cli.load_plan(tmp_plan_path)
        assert result is None
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err

    def test_save_plan(self, tmp_plan_path, empty_plan):
        """Test saving a plan updates timestamp and recalculates progress."""
        original_updated = empty_plan["meta"]["updated_at"]
        cli.save_plan(tmp_plan_path, empty_plan)

        loaded = json.loads(tmp_plan_path.read_text())
        assert loaded["meta"]["updated_at"] != original_updated

    def test_save_plan_with_tasks(self, tmp_plan_path, sample_plan):
        """Test saving recalculates progress correctly."""
        cli.save_plan(tmp_plan_path, sample_plan)
        loaded = json.loads(tmp_plan_path.read_text())
        assert loaded["summary"]["total_tasks"] == 4


# ============ PROGRESS CALCULATION ============


class TestProgressCalculation:
    """Tests for progress recalculation."""

    def test_recalculate_empty_plan(self, empty_plan):
        """Test recalculating progress with no phases."""
        cli.recalculate_progress(empty_plan)
        assert empty_plan["summary"]["total_tasks"] == 0
        assert empty_plan["summary"]["completed_tasks"] == 0
        assert empty_plan["summary"]["overall_progress"] == 0

    def test_recalculate_with_tasks(self, sample_plan):
        """Test recalculating progress with tasks."""
        cli.recalculate_progress(sample_plan)
        assert sample_plan["summary"]["total_tasks"] == 4
        assert sample_plan["summary"]["completed_tasks"] == 1
        assert sample_plan["summary"]["overall_progress"] == 25.0

    def test_recalculate_all_completed(self, completed_plan):
        """Test recalculating progress when all tasks are done."""
        cli.recalculate_progress(completed_plan)
        assert completed_plan["summary"]["overall_progress"] == 100.0
        assert completed_plan["phases"][0]["status"] == "completed"

    def test_recalculate_phase_status_in_progress(self, sample_plan):
        """Test phase status becomes in_progress when tasks are partially done."""
        cli.recalculate_progress(sample_plan)
        assert sample_plan["phases"][0]["status"] == "in_progress"

    def test_recalculate_empty_phase(self):
        """Test recalculating with empty phase (no tasks)."""
        plan = {
            "meta": {},
            "summary": {},
            "phases": [
                {
                    "id": "0",
                    "name": "Empty",
                    "description": "No tasks",
                    "status": "pending",
                    "progress": {},
                    "tasks": [],
                }
            ],
        }
        cli.recalculate_progress(plan)
        assert plan["phases"][0]["progress"]["percentage"] == 0


# ============ TASK/PHASE FINDING ============


class TestFinding:
    """Tests for task and phase finding functions."""

    def test_get_current_phase_in_progress(self, sample_plan):
        """Test finding current phase when one is in progress."""
        phase = cli.get_current_phase(sample_plan)
        assert phase is not None
        assert phase["id"] == "0"
        assert phase["status"] == "in_progress"

    def test_get_current_phase_pending(self, empty_plan):
        """Test finding current phase returns None when no phases."""
        phase = cli.get_current_phase(empty_plan)
        assert phase is None

    def test_get_current_phase_first_pending(self):
        """Test returns first pending phase when none in progress."""
        plan = {
            "phases": [
                {"id": "0", "status": "completed"},
                {"id": "1", "status": "pending"},
            ]
        }
        phase = cli.get_current_phase(plan)
        assert phase["id"] == "1"

    def test_get_next_task_in_progress(self, sample_plan):
        """Test finding next task returns in_progress task first."""
        result = cli.get_next_task(sample_plan)
        assert result is not None
        _phase, task = result
        assert task["status"] == "in_progress"
        assert task["id"] == "0.1.2"

    def test_get_next_task_pending_with_deps_met(self, sample_plan):
        """Test finding next pending task with all dependencies met."""
        # Mark in_progress task as completed
        sample_plan["phases"][0]["tasks"][1]["status"] = "completed"
        result = cli.get_next_task(sample_plan)
        assert result is not None
        _phase, task = result
        # get_next_task processes phases in order, so Phase 1 is checked
        # Task 1.1.1 depends on 0.1.2 which is now completed, so it's eligible
        assert task["id"] == "1.1.1"

    def test_get_next_task_skips_completed_phases(self, completed_plan):
        """Test skips completed phases when finding next task."""
        result = cli.get_next_task(completed_plan)
        assert result is None

    def test_get_next_task_skips_skipped_phases(self, plan_with_skipped):
        """Test skips skipped phases when finding next task."""
        result = cli.get_next_task(plan_with_skipped)
        assert result is None

    def test_get_next_task_unmet_deps(self):
        """Test task with unmet dependencies is skipped."""
        plan = {
            "phases": [
                {
                    "id": "0",
                    "status": "in_progress",
                    "tasks": [
                        {"id": "0.1.1", "status": "pending", "depends_on": ["0.1.2"]},
                        {"id": "0.1.2", "status": "pending", "depends_on": []},
                    ],
                }
            ]
        }
        result = cli.get_next_task(plan)
        _phase, task = result
        assert task["id"] == "0.1.2"  # This one has no deps

    def test_find_task_exists(self, sample_plan):
        """Test finding an existing task by ID."""
        result = cli.find_task(sample_plan, "0.1.1")
        assert result is not None
        _phase, task = result
        assert task["title"] == "Task One"

    def test_find_task_not_found(self, sample_plan):
        """Test finding a non-existent task."""
        result = cli.find_task(sample_plan, "99.99.99")
        assert result is None

    def test_find_phase_exists(self, sample_plan):
        """Test finding an existing phase by ID."""
        phase = cli.find_phase(sample_plan, "0")
        assert phase is not None
        assert phase["name"] == "Setup"

    def test_find_phase_not_found(self, sample_plan):
        """Test finding a non-existent phase."""
        phase = cli.find_phase(sample_plan, "99")
        assert phase is None

    def test_task_to_dict(self, sample_plan):
        """Test converting task to dictionary format."""
        phase = sample_plan["phases"][0]
        task = phase["tasks"][0]
        result = cli.task_to_dict(phase, task)
        assert result["id"] == "0.1.1"
        assert result["phase_id"] == "0"
        assert result["phase_name"] == "Setup"


# ============ VIEW COMMANDS ============


class TestViewCommands:
    """Tests for view commands."""

    def test_cmd_overview_text(self, sample_plan, capsys):
        """Test overview command text output."""
        cli.cmd_overview(sample_plan, as_json=False)
        captured = capsys.readouterr()
        assert "Test Project" in captured.out
        assert "Phase 0" in captured.out

    def test_cmd_overview_json(self, sample_plan, capsys):
        """Test overview command JSON output."""
        cli.cmd_overview(sample_plan, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["meta"]["project"] == "Test Project"

    def test_cmd_current_text(self, sample_plan, capsys):
        """Test current command text output."""
        cli.cmd_current(sample_plan, as_json=False)
        captured = capsys.readouterr()
        assert "Test Project" in captured.out
        assert "Next:" in captured.out

    def test_cmd_current_json(self, sample_plan, capsys):
        """Test current command JSON output."""
        cli.cmd_current(sample_plan, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "summary" in result
        assert "current_phase" in result
        assert "next_task" in result

    def test_cmd_current_no_next_task(self, completed_plan, capsys):
        """Test current command when no next task available."""
        cli.cmd_current(completed_plan, as_json=False)
        captured = capsys.readouterr()
        assert "Next:" not in captured.out

    def test_cmd_current_no_current_phase(self, completed_plan, capsys):
        """Test current command when no current phase (all completed)."""
        cli.cmd_current(completed_plan, as_json=False)
        captured = capsys.readouterr()
        assert "100%" in captured.out

    def test_cmd_next_text(self, sample_plan, capsys):
        """Test next command text output."""
        cli.cmd_next(sample_plan, as_json=False)
        captured = capsys.readouterr()
        assert "Next Task:" in captured.out
        assert "0.1.2" in captured.out

    def test_cmd_next_json(self, sample_plan, capsys):
        """Test next command JSON output."""
        cli.cmd_next(sample_plan, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["id"] == "0.1.2"

    def test_cmd_next_no_tasks(self, completed_plan, capsys):
        """Test next command when no pending tasks."""
        cli.cmd_next(completed_plan, as_json=False)
        captured = capsys.readouterr()
        assert "No pending tasks" in captured.out

    def test_cmd_next_no_tasks_json(self, completed_plan, capsys):
        """Test next command JSON when no pending tasks."""
        cli.cmd_next(completed_plan, as_json=True)
        captured = capsys.readouterr()
        assert captured.out.strip() == "null"

    def test_cmd_next_with_deps(self, sample_plan, capsys):
        """Test next command shows dependencies."""
        cli.cmd_next(sample_plan, as_json=False)
        captured = capsys.readouterr()
        assert "Depends on:" in captured.out

    def test_cmd_phase_text(self, sample_plan, capsys):
        """Test phase command text output."""
        cli.cmd_phase(sample_plan, as_json=False)
        captured = capsys.readouterr()
        assert "Phase 0: Setup" in captured.out
        assert "0.1.1" in captured.out

    def test_cmd_phase_json(self, sample_plan, capsys):
        """Test phase command JSON output."""
        cli.cmd_phase(sample_plan, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["id"] == "0"

    def test_cmd_phase_no_active(self, completed_plan, capsys):
        """Test phase command when no active phase."""
        cli.cmd_phase(completed_plan, as_json=False)
        captured = capsys.readouterr()
        assert "No active phase" in captured.out

    def test_cmd_phase_no_active_json(self, completed_plan, capsys):
        """Test phase command JSON when no active phase."""
        cli.cmd_phase(completed_plan, as_json=True)
        captured = capsys.readouterr()
        assert captured.out.strip() == "null"

    def test_cmd_get_text(self, sample_plan, capsys):
        """Test get command text output."""
        cli.cmd_get(sample_plan, "0.1.1", as_json=False)
        captured = capsys.readouterr()
        assert "Task One" in captured.out
        assert "completed" in captured.out

    def test_cmd_get_json(self, sample_plan, capsys):
        """Test get command JSON output."""
        cli.cmd_get(sample_plan, "0.1.1", as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["id"] == "0.1.1"

    def test_cmd_get_not_found(self, sample_plan, capsys):
        """Test get command for non-existent task."""
        cli.cmd_get(sample_plan, "99.99.99", as_json=False)
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_cmd_get_not_found_json(self, sample_plan, capsys):
        """Test get command JSON for non-existent task."""
        cli.cmd_get(sample_plan, "99.99.99", as_json=True)
        captured = capsys.readouterr()
        assert captured.out.strip() == "null"

    def test_cmd_get_with_tracking(self, sample_plan, capsys):
        """Test get command shows tracking info."""
        cli.cmd_get(sample_plan, "0.1.1", as_json=False)
        captured = capsys.readouterr()
        assert "Completed:" in captured.out

    def test_cmd_get_with_started_tracking(self, sample_plan, capsys):
        """Test get command shows started_at tracking."""
        cli.cmd_get(sample_plan, "0.1.2", as_json=False)
        captured = capsys.readouterr()
        assert "Started:" in captured.out

    def test_cmd_last_text(self, sample_plan, capsys):
        """Test last command text output."""
        cli.cmd_last(sample_plan, count=5, as_json=False)
        captured = capsys.readouterr()
        assert "Recently Completed:" in captured.out
        assert "0.1.1" in captured.out

    def test_cmd_last_json(self, sample_plan, capsys):
        """Test last command JSON output."""
        cli.cmd_last(sample_plan, count=5, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert len(result) == 1
        assert result[0]["id"] == "0.1.1"

    def test_cmd_last_no_completed(self, empty_plan, capsys):
        """Test last command when no completed tasks."""
        cli.cmd_last(empty_plan, count=5, as_json=False)
        captured = capsys.readouterr()
        assert "No completed tasks" in captured.out

    def test_cmd_last_no_completed_json(self, empty_plan, capsys):
        """Test last command JSON when no completed tasks."""
        cli.cmd_last(empty_plan, count=5, as_json=True)
        captured = capsys.readouterr()
        assert captured.out.strip() == "[]"

    def test_cmd_last_with_limit(self, completed_plan, capsys):
        """Test last command respects count limit."""
        cli.cmd_last(completed_plan, count=1, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert len(result) == 1

    def test_cmd_last_sorts_by_completion(self, completed_plan, capsys):
        """Test last command sorts by completion time."""
        cli.cmd_last(completed_plan, count=5, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        # Most recent first (0.1.2 completed on Jan 3)
        assert result[0]["id"] == "0.1.2"

    def test_cmd_last_handles_missing_timestamp(self):
        """Test last command handles tasks without completion timestamps."""
        plan = {
            "phases": [
                {
                    "id": "0",
                    "name": "Test",
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "No time",
                            "status": "completed",
                            "tracking": {},
                        }
                    ],
                }
            ]
        }
        output = StringIO()
        with patch("sys.stdout", output):
            cli.cmd_last(plan, count=5, as_json=False)
        assert "unknown" in output.getvalue()


class TestValidateCommand:
    """Tests for validate command."""

    def test_load_schema(self):
        """Test schema loading from package resources."""
        schema = cli.load_schema()
        assert "$schema" in schema
        assert "properties" in schema

    def test_cmd_validate_success(self, sample_plan_file, capsys):
        """Test validate command with valid plan."""
        plan = cli.load_plan(sample_plan_file)
        cli.cmd_validate(plan, sample_plan_file, as_json=False)
        captured = capsys.readouterr()
        assert "is valid" in captured.out

    def test_cmd_validate_success_json(self, sample_plan_file, capsys):
        """Test validate command JSON with valid plan."""
        plan = cli.load_plan(sample_plan_file)
        cli.cmd_validate(plan, sample_plan_file, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["valid"] is True

    def test_cmd_validate_failure(self, tmp_plan_path, capsys):
        """Test validate command with invalid plan."""
        invalid_plan = {"invalid": "structure"}
        tmp_plan_path.write_text(json.dumps(invalid_plan))
        with pytest.raises(SystemExit):
            cli.cmd_validate(invalid_plan, tmp_plan_path, as_json=False)
        captured = capsys.readouterr()
        assert "Validation failed" in captured.out

    def test_cmd_validate_failure_json(self, tmp_plan_path, capsys):
        """Test validate command JSON with invalid plan."""
        invalid_plan = {"invalid": "structure"}
        tmp_plan_path.write_text(json.dumps(invalid_plan))
        with pytest.raises(SystemExit):
            cli.cmd_validate(invalid_plan, tmp_plan_path, as_json=True)
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["valid"] is False

    def test_cmd_validate_shows_path(self, tmp_plan_path, capsys):
        """Test validate error shows JSON path for nested error."""
        # Create a plan with an invalid nested value to trigger absolute_path
        invalid_plan = {
            "meta": {
                "project": "Test",
                "version": "not-semver",  # Invalid version format
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "business_plan_path": ".claude/BUSINESS_PLAN.md",
            },
            "summary": {
                "total_phases": 0,
                "total_tasks": 0,
                "completed_tasks": 0,
                "overall_progress": 0,
            },
            "phases": [],
        }
        tmp_plan_path.write_text(json.dumps(invalid_plan))
        with pytest.raises(SystemExit):
            cli.cmd_validate(invalid_plan, tmp_plan_path, as_json=False)
        captured = capsys.readouterr()
        # Should show the path to the invalid field
        assert "Path:" in captured.out


# ============ EDIT COMMANDS ============


class TestEditCommands:
    """Tests for edit commands."""

    def test_cmd_init_creates_file(self, tmp_plan_path, capsys):
        """Test init creates a new plan file."""
        args = Namespace(file=tmp_plan_path, name="New Project", force=False)
        cli.cmd_init(args)
        assert tmp_plan_path.exists()
        captured = capsys.readouterr()
        assert "Created" in captured.out

    def test_cmd_init_refuses_overwrite(self, sample_plan_file, capsys):
        """Test init refuses to overwrite existing file without force."""
        args = Namespace(file=sample_plan_file, name="New Project", force=False)
        with pytest.raises(SystemExit):
            cli.cmd_init(args)
        captured = capsys.readouterr()
        assert "already exists" in captured.err

    def test_cmd_init_force_overwrite(self, sample_plan_file, capsys):
        """Test init can overwrite with force flag."""
        args = Namespace(file=sample_plan_file, name="Forced Project", force=True)
        cli.cmd_init(args)
        plan = json.loads(sample_plan_file.read_text())
        assert plan["meta"]["project"] == "Forced Project"

    def test_cmd_add_phase(self, empty_plan_file, capsys):
        """Test adding a new phase."""
        args = Namespace(file=empty_plan_file, name="New Phase", desc="Description")
        cli.cmd_add_phase(args)
        captured = capsys.readouterr()
        assert "Added Phase" in captured.out
        plan = json.loads(empty_plan_file.read_text())
        assert len(plan["phases"]) == 1
        assert plan["phases"][0]["name"] == "New Phase"

    def test_cmd_add_phase_increments_id(self, sample_plan_file, capsys):
        """Test phase ID increments correctly."""
        args = Namespace(file=sample_plan_file, name="Phase 3", desc=None)
        cli.cmd_add_phase(args)
        plan = json.loads(sample_plan_file.read_text())
        # Sample plan has phases 0 and 1, new should be 2
        assert plan["phases"][-1]["id"] == "2"

    def test_cmd_add_phase_file_not_found(self, tmp_path, capsys):
        """Test add_phase with non-existent file."""
        args = Namespace(file=tmp_path / "nonexistent.json", name="Test", desc=None)
        with pytest.raises(SystemExit):
            cli.cmd_add_phase(args)

    def test_cmd_add_task(self, sample_plan_file, capsys):
        """Test adding a new task."""
        args = Namespace(
            file=sample_plan_file,
            phase="0",
            title="New Task",
            agent="tester",
            deps=None,
        )
        cli.cmd_add_task(args)
        captured = capsys.readouterr()
        assert "Added" in captured.out
        plan = json.loads(sample_plan_file.read_text())
        assert len(plan["phases"][0]["tasks"]) == 3

    def test_cmd_add_task_with_deps(self, sample_plan_file, capsys):
        """Test adding task with dependencies."""
        args = Namespace(
            file=sample_plan_file,
            phase="0",
            title="Dependent Task",
            agent=None,
            deps="0.1.1,0.1.2",
        )
        cli.cmd_add_task(args)
        plan = json.loads(sample_plan_file.read_text())
        new_task = plan["phases"][0]["tasks"][-1]
        assert new_task["depends_on"] == ["0.1.1", "0.1.2"]

    def test_cmd_add_task_to_empty_phase(self, empty_plan_file, capsys):
        """Test adding first task to an empty phase."""
        # First add a phase
        args = Namespace(file=empty_plan_file, name="Phase", desc="Test")
        cli.cmd_add_phase(args)

        # Then add task
        args = Namespace(
            file=empty_plan_file,
            phase="0",
            title="First Task",
            agent=None,
            deps=None,
        )
        cli.cmd_add_task(args)
        plan = json.loads(empty_plan_file.read_text())
        assert plan["phases"][0]["tasks"][0]["id"] == "0.1.1"

    def test_cmd_add_task_phase_not_found(self, sample_plan_file, capsys):
        """Test adding task to non-existent phase."""
        args = Namespace(
            file=sample_plan_file,
            phase="99",
            title="Task",
            agent=None,
            deps=None,
        )
        with pytest.raises(SystemExit):
            cli.cmd_add_task(args)
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_cmd_add_task_file_not_found(self, tmp_path, capsys):
        """Test add_task with non-existent file."""
        args = Namespace(
            file=tmp_path / "nonexistent.json",
            phase="0",
            title="Task",
            agent=None,
            deps=None,
        )
        with pytest.raises(SystemExit):
            cli.cmd_add_task(args)

    def test_cmd_set_status(self, sample_plan_file, capsys):
        """Test setting task status."""
        args = Namespace(file=sample_plan_file, id="0.1.2", field="status", value="completed")
        cli.cmd_set(args)
        captured = capsys.readouterr()
        assert "status" in captured.out
        plan = json.loads(sample_plan_file.read_text())
        task = plan["phases"][0]["tasks"][1]
        assert task["status"] == "completed"
        assert "completed_at" in task["tracking"]

    def test_cmd_set_status_in_progress(self, sample_plan_file, capsys):
        """Test setting task status to in_progress adds started_at."""
        args = Namespace(file=sample_plan_file, id="1.1.1", field="status", value="in_progress")
        cli.cmd_set(args)
        plan = json.loads(sample_plan_file.read_text())
        task = plan["phases"][1]["tasks"][0]
        assert task["status"] == "in_progress"
        assert "started_at" in task["tracking"]

    def test_cmd_set_invalid_status(self, sample_plan_file, capsys):
        """Test setting invalid status fails."""
        args = Namespace(file=sample_plan_file, id="0.1.1", field="status", value="invalid")
        with pytest.raises(SystemExit):
            cli.cmd_set(args)
        captured = capsys.readouterr()
        assert "Invalid status" in captured.err

    def test_cmd_set_agent(self, sample_plan_file, capsys):
        """Test setting task agent."""
        args = Namespace(file=sample_plan_file, id="0.1.1", field="agent", value="new-agent")
        cli.cmd_set(args)
        plan = json.loads(sample_plan_file.read_text())
        assert plan["phases"][0]["tasks"][0]["agent_type"] == "new-agent"

    def test_cmd_set_agent_none(self, sample_plan_file, capsys):
        """Test setting agent to none clears it."""
        args = Namespace(file=sample_plan_file, id="0.1.1", field="agent", value="none")
        cli.cmd_set(args)
        plan = json.loads(sample_plan_file.read_text())
        assert plan["phases"][0]["tasks"][0]["agent_type"] is None

    def test_cmd_set_title(self, sample_plan_file, capsys):
        """Test setting task title."""
        args = Namespace(file=sample_plan_file, id="0.1.1", field="title", value="New Title")
        cli.cmd_set(args)
        plan = json.loads(sample_plan_file.read_text())
        assert plan["phases"][0]["tasks"][0]["title"] == "New Title"

    def test_cmd_set_invalid_field(self, sample_plan_file, capsys):
        """Test setting invalid field fails."""
        args = Namespace(file=sample_plan_file, id="0.1.1", field="invalid", value="value")
        with pytest.raises(SystemExit):
            cli.cmd_set(args)
        captured = capsys.readouterr()
        assert "Unknown field" in captured.err

    def test_cmd_set_task_not_found(self, sample_plan_file, capsys):
        """Test setting non-existent task fails."""
        args = Namespace(file=sample_plan_file, id="99.99.99", field="status", value="completed")
        with pytest.raises(SystemExit):
            cli.cmd_set(args)
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_cmd_set_file_not_found(self, tmp_path, capsys):
        """Test cmd_set with non-existent file."""
        args = Namespace(file=tmp_path / "nonexistent.json", id="0.1.1", field="status", value="completed")
        with pytest.raises(SystemExit):
            cli.cmd_set(args)

    def test_cmd_done(self, sample_plan_file, capsys):
        """Test done command marks task completed."""
        args = Namespace(file=sample_plan_file, id="0.1.2")
        cli.cmd_done(args)
        plan = json.loads(sample_plan_file.read_text())
        assert plan["phases"][0]["tasks"][1]["status"] == "completed"

    def test_cmd_start(self, sample_plan_file, capsys):
        """Test start command marks task in_progress."""
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_start(args)
        plan = json.loads(sample_plan_file.read_text())
        assert plan["phases"][1]["tasks"][0]["status"] == "in_progress"

    def test_cmd_block(self, sample_plan_file, capsys):
        """Test block command marks task blocked."""
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_block(args)
        plan = json.loads(sample_plan_file.read_text())
        assert plan["phases"][1]["tasks"][0]["status"] == "blocked"

    def test_cmd_skip(self, sample_plan_file, capsys):
        """Test skip command marks task skipped."""
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_skip(args)
        plan = json.loads(sample_plan_file.read_text())
        assert plan["phases"][1]["tasks"][0]["status"] == "skipped"

    def test_cmd_defer(self, sample_plan_file, capsys):
        """Test defer command moves task to deferred phase."""
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_defer(args)
        captured = capsys.readouterr()
        assert "deferred" in captured.out
        plan = json.loads(sample_plan_file.read_text())
        # Task should be removed from original phase
        assert len(plan["phases"][1]["tasks"]) == 1
        # Deferred phase should exist with the task
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        assert len(deferred["tasks"]) == 1
        assert deferred["tasks"][0]["title"] == "Feature X"
        assert deferred["tasks"][0]["id"] == "deferred.1.1"

    def test_cmd_defer_creates_phase(self, sample_plan_file, capsys):
        """Test defer creates deferred phase if it doesn't exist."""
        plan = json.loads(sample_plan_file.read_text())
        assert not any(p["id"] == "deferred" for p in plan["phases"])
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_defer(args)
        plan = json.loads(sample_plan_file.read_text())
        assert any(p["id"] == "deferred" for p in plan["phases"])

    def test_cmd_defer_uses_existing_phase(self, sample_plan_file, capsys):
        """Test defer reuses existing deferred phase and increments ID."""
        # Defer first task
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_defer(args)
        # Defer second task
        args = Namespace(file=sample_plan_file, id="1.1.2")
        cli.cmd_defer(args)
        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        assert len(deferred["tasks"]) == 2
        # Second task should have incremented ID
        assert deferred["tasks"][1]["id"] == "deferred.1.2"

    def test_cmd_defer_handles_malformed_ids(self, tmp_plan_path, capsys):
        """Test defer handles existing tasks with malformed IDs."""
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
                        {"id": "0.1.1", "title": "Task", "status": "pending",
                         "agent_type": None, "depends_on": [], "tracking": {}},
                    ],
                },
                {
                    "id": "deferred",
                    "name": "Deferred",
                    "description": "Deferred tasks",
                    "status": "pending",
                    "progress": {"completed": 0, "total": 2, "percentage": 0},
                    "tasks": [
                        {"id": "short", "title": "Short ID", "status": "pending",
                         "agent_type": None, "depends_on": [], "tracking": {}},
                        {"id": "deferred.x.y", "title": "Non-numeric", "status": "pending",
                         "agent_type": None, "depends_on": [], "tracking": {}},
                    ],
                },
            ],
        }
        tmp_plan_path.write_text(json.dumps(plan))
        args = Namespace(file=tmp_plan_path, id="0.1.1")
        cli.cmd_defer(args)
        result = json.loads(tmp_plan_path.read_text())
        deferred = next(p for p in result["phases"] if p["id"] == "deferred")
        # Should still work, defaulting to 1 for the new task
        assert deferred["tasks"][2]["id"] == "deferred.1.1"

    def test_cmd_defer_task_not_found(self, sample_plan_file, capsys):
        """Test defer with non-existent task fails."""
        args = Namespace(file=sample_plan_file, id="99.99.99")
        with pytest.raises(SystemExit):
            cli.cmd_defer(args)
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_cmd_defer_file_not_found(self, tmp_path, capsys):
        """Test defer with non-existent file fails."""
        args = Namespace(file=tmp_path / "nonexistent.json", id="0.1.1")
        with pytest.raises(SystemExit):
            cli.cmd_defer(args)

    def test_cmd_rm_task(self, sample_plan_file, capsys):
        """Test removing a task."""
        args = Namespace(file=sample_plan_file, type="task", id="0.1.1")
        cli.cmd_rm(args)
        captured = capsys.readouterr()
        assert "Removed task" in captured.out
        plan = json.loads(sample_plan_file.read_text())
        assert len(plan["phases"][0]["tasks"]) == 1

    def test_cmd_rm_task_not_found(self, sample_plan_file, capsys):
        """Test removing non-existent task fails."""
        args = Namespace(file=sample_plan_file, type="task", id="99.99.99")
        with pytest.raises(SystemExit):
            cli.cmd_rm(args)
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_cmd_rm_phase(self, sample_plan_file, capsys):
        """Test removing a phase."""
        args = Namespace(file=sample_plan_file, type="phase", id="1")
        cli.cmd_rm(args)
        captured = capsys.readouterr()
        assert "Removed phase" in captured.out
        plan = json.loads(sample_plan_file.read_text())
        assert len(plan["phases"]) == 1

    def test_cmd_rm_phase_not_found(self, sample_plan_file, capsys):
        """Test removing non-existent phase fails."""
        args = Namespace(file=sample_plan_file, type="phase", id="99")
        with pytest.raises(SystemExit):
            cli.cmd_rm(args)
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_cmd_rm_file_not_found(self, tmp_path, capsys):
        """Test cmd_rm with non-existent file."""
        args = Namespace(file=tmp_path / "nonexistent.json", type="task", id="0.1.1")
        with pytest.raises(SystemExit):
            cli.cmd_rm(args)


# ============ CLI MAIN ============


class TestCLIMain:
    """Tests for main CLI entry point."""

    def test_main_help(self, capsys, monkeypatch):
        """Test --help flag shows help."""
        monkeypatch.setattr(sys, "argv", ["pv", "--help"])
        cli.main()
        captured = capsys.readouterr()
        assert "View and edit plan.json" in captured.out

    def test_main_help_command(self, capsys, monkeypatch):
        """Test help command shows help."""
        monkeypatch.setattr(sys, "argv", ["pv", "help"])
        cli.main()
        captured = capsys.readouterr()
        assert "View and edit plan.json" in captured.out

    def test_main_h_alias(self, capsys, monkeypatch):
        """Test h alias for help."""
        monkeypatch.setattr(sys, "argv", ["pv", "h"])
        cli.main()
        captured = capsys.readouterr()
        assert "View and edit plan.json" in captured.out

    def test_main_overview_default(self, sample_plan_file, capsys, monkeypatch):
        """Test default command is overview."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file)])
        cli.main()
        captured = capsys.readouterr()
        assert "Test Project" in captured.out

    def test_main_current(self, sample_plan_file, capsys, monkeypatch):
        """Test current command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "current"])
        cli.main()
        captured = capsys.readouterr()
        assert "Test Project" in captured.out

    def test_main_c_alias(self, sample_plan_file, capsys, monkeypatch):
        """Test c alias for current."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "c"])
        cli.main()
        captured = capsys.readouterr()
        assert "Test Project" in captured.out

    def test_main_next(self, sample_plan_file, capsys, monkeypatch):
        """Test next command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "next"])
        cli.main()
        captured = capsys.readouterr()
        assert "Next Task" in captured.out

    def test_main_n_alias(self, sample_plan_file, capsys, monkeypatch):
        """Test n alias for next."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "n"])
        cli.main()
        captured = capsys.readouterr()
        assert "Next Task" in captured.out

    def test_main_phase(self, sample_plan_file, capsys, monkeypatch):
        """Test phase command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "phase"])
        cli.main()
        captured = capsys.readouterr()
        assert "Phase 0" in captured.out

    def test_main_p_alias(self, sample_plan_file, capsys, monkeypatch):
        """Test p alias for phase."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "p"])
        cli.main()
        captured = capsys.readouterr()
        assert "Phase 0" in captured.out

    def test_main_get(self, sample_plan_file, capsys, monkeypatch):
        """Test get command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "get", "0.1.1"])
        cli.main()
        captured = capsys.readouterr()
        assert "Task One" in captured.out

    def test_main_g_alias(self, sample_plan_file, capsys, monkeypatch):
        """Test g alias for get."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "g", "0.1.1"])
        cli.main()
        captured = capsys.readouterr()
        assert "Task One" in captured.out

    def test_main_last(self, sample_plan_file, capsys, monkeypatch):
        """Test last command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "last"])
        cli.main()
        captured = capsys.readouterr()
        assert "Recently Completed" in captured.out

    def test_main_l_alias(self, sample_plan_file, capsys, monkeypatch):
        """Test l alias for last."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "l"])
        cli.main()
        captured = capsys.readouterr()
        assert "Recently Completed" in captured.out

    def test_main_last_with_count(self, sample_plan_file, capsys, monkeypatch):
        """Test last command with -n option."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "last", "-n", "1"])
        cli.main()
        captured = capsys.readouterr()
        assert "Recently Completed" in captured.out

    def test_main_validate(self, sample_plan_file, capsys, monkeypatch):
        """Test validate command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "validate"])
        cli.main()
        captured = capsys.readouterr()
        assert "is valid" in captured.out

    def test_main_v_alias(self, sample_plan_file, capsys, monkeypatch):
        """Test v alias for validate."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "v"])
        cli.main()
        captured = capsys.readouterr()
        assert "is valid" in captured.out

    def test_main_init(self, tmp_plan_path, capsys, monkeypatch):
        """Test init command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(tmp_plan_path), "init", "My Project"])
        cli.main()
        captured = capsys.readouterr()
        assert "Created" in captured.out

    def test_main_init_force(self, sample_plan_file, capsys, monkeypatch):
        """Test init command with --force."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "init", "New", "--force"])
        cli.main()
        captured = capsys.readouterr()
        assert "Created" in captured.out

    def test_main_add_phase(self, empty_plan_file, capsys, monkeypatch):
        """Test add-phase command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(empty_plan_file), "add-phase", "Phase 1"])
        cli.main()
        captured = capsys.readouterr()
        assert "Added Phase" in captured.out

    def test_main_add_phase_with_desc(self, empty_plan_file, capsys, monkeypatch):
        """Test add-phase command with description."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["pv", "-f", str(empty_plan_file), "add-phase", "Phase 1", "--desc", "Description"],
        )
        cli.main()
        captured = capsys.readouterr()
        assert "Added Phase" in captured.out

    def test_main_add_task(self, sample_plan_file, capsys, monkeypatch):
        """Test add-task command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "add-task", "0", "New Task"])
        cli.main()
        captured = capsys.readouterr()
        assert "Added" in captured.out

    def test_main_add_task_with_options(self, sample_plan_file, capsys, monkeypatch):
        """Test add-task command with agent and deps."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "pv",
                "-f",
                str(sample_plan_file),
                "add-task",
                "0",
                "Task",
                "--agent",
                "tester",
                "--deps",
                "0.1.1",
            ],
        )
        cli.main()
        captured = capsys.readouterr()
        assert "Added" in captured.out

    def test_main_set(self, sample_plan_file, capsys, monkeypatch):
        """Test set command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "set", "0.1.1", "status", "blocked"])
        cli.main()
        captured = capsys.readouterr()
        assert "status" in captured.out

    def test_main_done(self, sample_plan_file, capsys, monkeypatch):
        """Test done command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "done", "0.1.2"])
        cli.main()
        captured = capsys.readouterr()
        assert "completed" in captured.out

    def test_main_start(self, sample_plan_file, capsys, monkeypatch):
        """Test start command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "start", "1.1.1"])
        cli.main()
        captured = capsys.readouterr()
        assert "in_progress" in captured.out

    def test_main_block(self, sample_plan_file, capsys, monkeypatch):
        """Test block command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "block", "1.1.1"])
        cli.main()
        captured = capsys.readouterr()
        assert "blocked" in captured.out

    def test_main_skip(self, sample_plan_file, capsys, monkeypatch):
        """Test skip command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "skip", "1.1.1"])
        cli.main()
        captured = capsys.readouterr()
        assert "skipped" in captured.out

    def test_main_defer(self, sample_plan_file, capsys, monkeypatch):
        """Test defer command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "defer", "1.1.1"])
        cli.main()
        captured = capsys.readouterr()
        assert "deferred" in captured.out

    def test_main_rm_task(self, sample_plan_file, capsys, monkeypatch):
        """Test rm task command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "rm", "task", "0.1.1"])
        cli.main()
        captured = capsys.readouterr()
        assert "Removed task" in captured.out

    def test_main_rm_phase(self, sample_plan_file, capsys, monkeypatch):
        """Test rm phase command via CLI."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "rm", "phase", "1"])
        cli.main()
        captured = capsys.readouterr()
        assert "Removed phase" in captured.out

    def test_main_json_flag_global(self, sample_plan_file, capsys, monkeypatch):
        """Test --json flag at global level."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "--json", "current"])
        cli.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "summary" in result

    def test_main_json_flag_after_command(self, sample_plan_file, capsys, monkeypatch):
        """Test --json flag after command."""
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(sample_plan_file), "current", "--json"])
        cli.main()
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "summary" in result

    def test_main_file_not_found(self, tmp_path, capsys, monkeypatch):
        """Test error when plan file not found."""
        nonexistent = tmp_path / "nonexistent.json"
        monkeypatch.setattr(sys, "argv", ["pv", "-f", str(nonexistent)])
        with pytest.raises(SystemExit):
            cli.main()
        captured = capsys.readouterr()
        assert "not found" in captured.err


# ============ EDGE CASES ============


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_add_task_with_malformed_task_ids(self, tmp_plan_path, capsys):
        """Test adding task when existing tasks have malformed IDs (< 3 parts)."""
        # Create a plan with a task that has a malformed ID (less than 3 parts)
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
                    "progress": {"completed": 0, "total": 1, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1",  # Malformed ID - only 2 parts
                            "title": "Malformed Task",
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
        )
        cli.cmd_add_task(args)
        captured = capsys.readouterr()
        assert "Added" in captured.out

    def test_add_task_id_increment_same_section(self, tmp_plan_path, capsys):
        """Test task ID incrementing when multiple tasks in same section."""
        # Create plan with multiple tasks in same section to test both branches
        # of the comparison: section > max_section OR (section == max_section AND task_num > max_task)
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
                    "progress": {"completed": 0, "total": 3, "percentage": 0},
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "Task 1",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.3",  # Task 3 exists but task 2 doesn't
                            "title": "Task 3",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        },
                        {
                            "id": "0.1.2",  # Task 2 - lower number than max
                            "title": "Task 2",
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
        )
        cli.cmd_add_task(args)

        # Verify the new task got ID 0.1.4 (max was 3, so next is 4)
        result_plan = json.loads(tmp_plan_path.read_text())
        new_task = result_plan["phases"][0]["tasks"][-1]
        assert new_task["id"] == "0.1.4"

    def test_task_without_agent_type(self, sample_plan, capsys):
        """Test display handles task without agent_type."""
        sample_plan["phases"][0]["tasks"][0]["agent_type"] = None
        cli.cmd_overview(sample_plan, as_json=False)
        captured = capsys.readouterr()
        assert "(general)" in captured.out

    def test_phase_with_no_agent_in_task(self, sample_plan, capsys):
        """Test phase display when task has no agent."""
        sample_plan["phases"][0]["tasks"][0]["agent_type"] = None
        cli.cmd_phase(sample_plan, as_json=False)
        capsys.readouterr()
        # Should not crash

    def test_get_task_no_deps(self, sample_plan, capsys):
        """Test get command for task without dependencies."""
        cli.cmd_get(sample_plan, "0.1.1", as_json=False)
        captured = capsys.readouterr()
        # Task 0.1.1 has no deps, so "Depends on:" shouldn't appear
        assert "Depends on:" not in captured.out

    def test_get_task_with_deps(self, sample_plan, capsys):
        """Test get command for task with dependencies."""
        cli.cmd_get(sample_plan, "0.1.2", as_json=False)
        captured = capsys.readouterr()
        assert "Depends on:" in captured.out
        assert "0.1.1" in captured.out

    def test_next_task_no_deps_shown(self):
        """Test next command without dependencies doesn't show deps line."""
        plan = {
            "phases": [
                {
                    "id": "0",
                    "name": "Test",
                    "status": "in_progress",
                    "tasks": [
                        {
                            "id": "0.1.1",
                            "title": "No deps",
                            "status": "pending",
                            "agent_type": None,
                            "depends_on": [],
                            "tracking": {},
                        }
                    ],
                }
            ]
        }
        output = StringIO()
        with patch("sys.stdout", output):
            cli.cmd_next(plan, as_json=False)
        assert "Depends on:" not in output.getvalue()

    def test_overview_with_all_task_states(self, capsys):
        """Test overview displays all task status types correctly."""
        plan = {
            "meta": {"project": "States Test", "version": "1.0.0"},
            "summary": {"total_tasks": 5, "completed_tasks": 1, "overall_progress": 20},
            "phases": [
                {
                    "id": "0",
                    "name": "All States",
                    "description": "Test",
                    "status": "in_progress",
                    "progress": {"completed": 1, "total": 5, "percentage": 20},
                    "tasks": [
                        {"id": "0.1.1", "title": "Done", "status": "completed", "agent_type": None},
                        {"id": "0.1.2", "title": "Working", "status": "in_progress", "agent_type": None},
                        {"id": "0.1.3", "title": "Waiting", "status": "pending", "agent_type": None},
                        {"id": "0.1.4", "title": "Stuck", "status": "blocked", "agent_type": None},
                        {"id": "0.1.5", "title": "Skipped", "status": "skipped", "agent_type": None},
                    ],
                }
            ],
        }
        cli.cmd_overview(plan, as_json=False)
        captured = capsys.readouterr()
        assert "\u2705" in captured.out  # completed
        assert "\U0001f504" in captured.out  # in_progress
        assert "\u23f3" in captured.out  # pending
        assert "\U0001f6d1" in captured.out  # blocked
        assert "\u23ed" in captured.out  # skipped
