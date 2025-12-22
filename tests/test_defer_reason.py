"""Tests for defer reason functionality."""

import json
import sys
from argparse import Namespace

from plan_view import cli


class TestDeferReason:
    """Tests for defer reason functionality."""

    def test_defer_with_reason_existing_task(self, sample_plan_file, capsys):
        """Test defer with reason for existing task."""
        args = Namespace(
            file=sample_plan_file,
            id="1.1.1",
            reason="Waiting for API documentation",
        )
        cli.cmd_defer(args)

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = deferred["tasks"][0]

        assert task["tracking"]["defer_reason"] == "Waiting for API documentation"

    def test_defer_with_reason_new_task(self, sample_plan_file, capsys):
        """Test defer with reason for new task."""
        args = Namespace(
            file=sample_plan_file,
            id="Fix authentication bug",
            reason="Low priority, focus on core features first",
        )
        cli.cmd_defer(args)

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = next(t for t in deferred["tasks"] if t["title"] == "Fix authentication bug")

        assert task["tracking"]["defer_reason"] == "Low priority, focus on core features first"

    def test_defer_without_reason(self, sample_plan_file, capsys):
        """Test defer without reason still works."""
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_defer(args)

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = deferred["tasks"][0]

        # Should not have defer_reason in tracking
        assert "defer_reason" not in task["tracking"]

    def test_defer_with_empty_reason(self, sample_plan_file, capsys):
        """Test defer with empty reason string."""
        args = Namespace(file=sample_plan_file, id="1.1.1", reason="")
        cli.cmd_defer(args)

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = deferred["tasks"][0]

        # Empty string should not be stored
        assert "defer_reason" not in task["tracking"]

    def test_defer_with_whitespace_only_reason(self, sample_plan_file, capsys):
        """Test defer with whitespace-only reason string."""
        args = Namespace(file=sample_plan_file, id="1.1.1", reason="   ")
        cli.cmd_defer(args)

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = deferred["tasks"][0]

        # Whitespace-only string should not be stored
        assert "defer_reason" not in task["tracking"]

    def test_deferred_view_shows_reason(self, sample_plan_file, capsys):
        """Test deferred view displays defer reason."""
        # Defer task with reason
        args = Namespace(
            file=sample_plan_file,
            id="1.1.1",
            reason="Blocked by external dependency",
        )
        cli.cmd_defer(args)

        # View deferred tasks
        plan = json.loads(sample_plan_file.read_text())
        cli.cmd_deferred(plan, as_json=False)
        captured = capsys.readouterr()

        assert "Blocked by external dependency" in captured.out
        assert "Reason:" in captured.out

    def test_deferred_view_without_reason(self, sample_plan_file, capsys):
        """Test deferred view without reason doesn't show extra line."""
        # Defer task without reason
        args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_defer(args)

        # View deferred tasks
        plan = json.loads(sample_plan_file.read_text())
        cli.cmd_deferred(plan, as_json=False)
        captured = capsys.readouterr()

        assert "Reason:" not in captured.out

    def test_get_task_shows_defer_reason(self, sample_plan_file, capsys):
        """Test get command shows defer reason for deferred task."""
        # Defer task with reason
        args = Namespace(
            file=sample_plan_file,
            id="1.1.1",
            reason="Needs design review",
        )
        cli.cmd_defer(args)

        # Get the deferred task
        plan = json.loads(sample_plan_file.read_text())
        cli.cmd_get(plan, "deferred.1.1", as_json=False)
        captured = capsys.readouterr()

        assert "Needs design review" in captured.out
        assert "Defer reason:" in captured.out

    def test_defer_reason_in_json_output(self, sample_plan_file, capsys):
        """Test defer reason appears in JSON output."""
        # Defer task with reason
        args = Namespace(
            file=sample_plan_file,
            id="1.1.1",
            reason="Technical debt to address later",
        )
        cli.cmd_defer(args)
        capsys.readouterr()  # Clear output from defer command

        # Get JSON output
        plan = json.loads(sample_plan_file.read_text())
        cli.cmd_deferred(plan, as_json=True)
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        task = output["tasks"][0]
        assert task["tracking"]["defer_reason"] == "Technical debt to address later"

    def test_defer_reason_with_special_characters(self, sample_plan_file, capsys):
        """Test defer reason with special characters."""
        args = Namespace(
            file=sample_plan_file,
            id="1.1.1",
            reason="Need to review v2.0 API & update docs (see #123)",
        )
        cli.cmd_defer(args)

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = deferred["tasks"][0]

        assert task["tracking"]["defer_reason"] == "Need to review v2.0 API & update docs (see #123)"

    def test_defer_reason_with_quiet_flag(self, sample_plan_file, capsys):
        """Test defer with reason and quiet flag suppresses output."""
        args = Namespace(
            file=sample_plan_file,
            id="1.1.1",
            reason="Testing quiet mode",
            quiet=True,
        )
        cli.cmd_defer(args)
        captured = capsys.readouterr()

        assert captured.out == ""

        # Verify reason was still stored
        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = deferred["tasks"][0]
        assert task["tracking"]["defer_reason"] == "Testing quiet mode"

    def test_defer_reason_with_dry_run(self, sample_plan_file, capsys):
        """Test defer with reason and dry-run doesn't save."""
        original = sample_plan_file.read_text()
        args = Namespace(
            file=sample_plan_file,
            id="1.1.1",
            reason="Testing dry run",
            dry_run=True,
            quiet=False,
        )
        cli.cmd_defer(args)
        captured = capsys.readouterr()

        assert "Would:" in captured.out
        # File should be unchanged
        assert sample_plan_file.read_text() == original

    def test_main_defer_with_reason_flag(self, sample_plan_file, capsys, monkeypatch):
        """Test defer via CLI with --reason flag."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "pv",
                "-f",
                str(sample_plan_file),
                "defer",
                "1.1.1",
                "--reason",
                "Waiting for code review",
            ],
        )
        cli.main()

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = deferred["tasks"][0]
        assert task["tracking"]["defer_reason"] == "Waiting for code review"

    def test_main_defer_with_reason_short_flag(self, sample_plan_file, capsys, monkeypatch):
        """Test defer via CLI with -r short flag."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "pv",
                "-f",
                str(sample_plan_file),
                "defer",
                "1.1.1",
                "-r",
                "Needs refactoring",
            ],
        )
        cli.main()

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = deferred["tasks"][0]
        assert task["tracking"]["defer_reason"] == "Needs refactoring"

    def test_multiple_defers_with_different_reasons(self, sample_plan_file, capsys):
        """Test multiple tasks deferred with different reasons."""
        # Defer first task
        args1 = Namespace(
            file=sample_plan_file,
            id="1.1.1",
            reason="Needs design review",
        )
        cli.cmd_defer(args1)

        # Defer second task
        args2 = Namespace(
            file=sample_plan_file,
            id="1.1.2",
            reason="Low priority feature",
        )
        cli.cmd_defer(args2)

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")

        assert len(deferred["tasks"]) == 2
        assert deferred["tasks"][0]["tracking"]["defer_reason"] == "Needs design review"
        assert deferred["tasks"][1]["tracking"]["defer_reason"] == "Low priority feature"

    def test_defer_preserves_other_tracking_fields(self, sample_plan_file, capsys):
        """Test defer with reason preserves other tracking fields."""
        # Start a task first
        start_args = Namespace(file=sample_plan_file, id="1.1.1")
        cli.cmd_start(start_args)

        # Then defer it with a reason
        defer_args = Namespace(
            file=sample_plan_file,
            id="1.1.1",
            reason="Reprioritized",
        )
        cli.cmd_defer(defer_args)

        plan = json.loads(sample_plan_file.read_text())
        deferred = next(p for p in plan["phases"] if p["id"] == "deferred")
        task = deferred["tasks"][0]

        # Should have both started_at and defer_reason
        assert "started_at" in task["tracking"]
        assert task["tracking"]["defer_reason"] == "Reprioritized"
