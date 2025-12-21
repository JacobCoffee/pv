"""Tests for decorator utilities."""

import json
from argparse import Namespace
from pathlib import Path

import pytest

from plan_view.decorators import require_plan


def test_require_plan_loads_and_injects_plan(tmp_path):
    """Test that @require_plan loads plan and injects it as first argument."""
    # Create a test plan file
    plan_path = tmp_path / "plan.json"
    plan_data = {
        "meta": {
            "project": "Test",
            "version": "1.0.0",
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
    plan_path.write_text(json.dumps(plan_data, indent=2))

    # Define a command function that expects plan as first arg
    @require_plan
    def test_cmd(plan: dict, args: Namespace) -> str:
        return f"Project: {plan['meta']['project']}"

    # Call with args only
    args = Namespace(file=plan_path)
    result = test_cmd(args)

    assert result == "Project: Test"


def test_require_plan_exits_on_missing_file(tmp_path):
    """Test that @require_plan exits with code 1 if plan file not found."""
    plan_path = tmp_path / "nonexistent.json"

    @require_plan
    def test_cmd(plan: dict, args: Namespace) -> None:
        pass

    args = Namespace(file=plan_path)

    with pytest.raises(SystemExit) as exc_info:
        test_cmd(args)

    assert exc_info.value.code == 1


def test_require_plan_exits_on_invalid_json(tmp_path):
    """Test that @require_plan exits with code 1 if JSON is invalid."""
    plan_path = tmp_path / "invalid.json"
    plan_path.write_text("{ invalid json }")

    @require_plan
    def test_cmd(plan: dict, args: Namespace) -> None:
        pass

    args = Namespace(file=plan_path)

    with pytest.raises(SystemExit) as exc_info:
        test_cmd(args)

    assert exc_info.value.code == 1


def test_require_plan_passes_extra_args(tmp_path):
    """Test that @require_plan correctly passes through additional arguments."""
    plan_path = tmp_path / "plan.json"
    plan_data = {
        "meta": {
            "project": "Test",
            "version": "1.0.0",
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
    plan_path.write_text(json.dumps(plan_data, indent=2))

    @require_plan
    def test_cmd(plan: dict, args: Namespace, extra_arg: str) -> str:
        return f"Project: {plan['meta']['project']}, Extra: {extra_arg}"

    args = Namespace(file=plan_path)
    result = test_cmd(args, "test_value")

    assert result == "Project: Test, Extra: test_value"


def test_require_plan_preserves_function_metadata(tmp_path):
    """Test that @require_plan preserves original function name and docstring."""

    @require_plan
    def sample_command(plan: dict, args: Namespace) -> None:
        """This is a sample command."""
        pass

    assert sample_command.__name__ == "sample_command"
    assert sample_command.__doc__ == "This is a sample command."


def test_require_plan_with_real_command_scenario(tmp_path):
    """Test @require_plan with a realistic command scenario that modifies plan."""
    plan_path = tmp_path / "plan.json"
    plan_data = {
        "meta": {
            "project": "Test",
            "version": "1.0.0",
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
    plan_path.write_text(json.dumps(plan_data, indent=2))

    @require_plan
    def add_test_phase(plan: dict, args: Namespace) -> None:
        """Add a test phase to the plan."""
        phase = {
            "id": "0",
            "name": args.phase_name,
            "description": "Test phase",
            "status": "pending",
            "progress": {"completed": 0, "total": 0, "percentage": 0},
            "tasks": [],
        }
        plan["phases"].append(phase)

    args = Namespace(file=plan_path, phase_name="Setup")
    add_test_phase(args)

    # Verify the function received and could modify the plan
    # Note: The plan object is modified in memory but not saved by the decorator
    # The actual save_plan call would be inside the real command function


def test_require_plan_extracts_file_from_namespace(tmp_path):
    """Test that decorator correctly extracts file path from args.file."""
    plan_path_1 = tmp_path / "plan1.json"
    plan_path_2 = tmp_path / "plan2.json"

    for path, project_name in [(plan_path_1, "Project1"), (plan_path_2, "Project2")]:
        plan_data = {
            "meta": {
                "project": project_name,
                "version": "1.0.0",
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
        path.write_text(json.dumps(plan_data, indent=2))

    @require_plan
    def get_project_name(plan: dict, args: Namespace) -> str:
        return plan["meta"]["project"]

    # Test with different file paths
    args1 = Namespace(file=plan_path_1)
    args2 = Namespace(file=plan_path_2)

    assert get_project_name(args1) == "Project1"
    assert get_project_name(args2) == "Project2"
