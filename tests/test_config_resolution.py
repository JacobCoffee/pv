"""Tests for monorepo config resolution (pyproject.toml and .pv.toml support)."""

import json
import os

import pytest

from plan_view.io import _find_config_file, resolve_plan_path


class TestFindConfigFile:
    """Tests for _find_config_file function."""

    def test_finds_pv_toml_in_current_dir(self, tmp_path):
        """Test finding .pv.toml in the current directory."""
        config = tmp_path / ".pv.toml"
        config.write_text('plan_file = "my-plan.json"\n')

        result = _find_config_file(tmp_path)
        assert result is not None
        config_path, config_dict = result
        assert config_path == config
        assert config_dict["plan_file"] == "my-plan.json"

    def test_finds_pyproject_toml_with_tool_pv(self, tmp_path):
        """Test finding pyproject.toml with [tool.pv] section."""
        config = tmp_path / "pyproject.toml"
        config.write_text('[tool.pv]\nplan_file = "plans/main.json"\n')

        result = _find_config_file(tmp_path)
        assert result is not None
        config_path, config_dict = result
        assert config_path == config
        assert config_dict["plan_file"] == "plans/main.json"

    def test_pv_toml_takes_precedence_over_pyproject(self, tmp_path):
        """Test that .pv.toml is preferred over pyproject.toml."""
        pv_toml = tmp_path / ".pv.toml"
        pv_toml.write_text('plan_file = "from-pv-toml.json"\n')

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.pv]\nplan_file = "from-pyproject.json"\n')

        result = _find_config_file(tmp_path)
        assert result is not None
        config_path, config_dict = result
        assert config_path == pv_toml
        assert config_dict["plan_file"] == "from-pv-toml.json"

    def test_ignores_pyproject_without_tool_pv(self, tmp_path):
        """Test that pyproject.toml without [tool.pv] is ignored."""
        config = tmp_path / "pyproject.toml"
        config.write_text('[project]\nname = "test"\n')

        result = _find_config_file(tmp_path)
        assert result is None

    def test_walks_up_to_parent_directories(self, tmp_path):
        """Test walking up directory tree to find config."""
        # Create config in parent
        config = tmp_path / ".pv.toml"
        config.write_text('plan_file = "plan.json"\n')

        # Create subdirectory
        subdir = tmp_path / "src" / "components"
        subdir.mkdir(parents=True)

        result = _find_config_file(subdir)
        assert result is not None
        config_path, _ = result
        assert config_path == config

    def test_returns_none_when_no_config_found(self, tmp_path):
        """Test returning None when no config file exists."""
        subdir = tmp_path / "empty"
        subdir.mkdir()

        result = _find_config_file(subdir)
        assert result is None

    def test_ignores_invalid_toml(self, tmp_path):
        """Test that invalid TOML files are skipped."""
        config = tmp_path / ".pv.toml"
        config.write_text("this is not valid toml {{{")

        result = _find_config_file(tmp_path)
        assert result is None


class TestResolvePlanPath:
    """Tests for resolve_plan_path function."""

    def test_explicit_path_overrides_config(self, tmp_path):
        """Test that explicit non-default path ignores config."""
        config = tmp_path / ".pv.toml"
        config.write_text('plan_file = "config-plan.json"\n')

        explicit = tmp_path / "explicit.json"
        result = resolve_plan_path(explicit)
        assert result == explicit

    def test_uses_config_plan_file(self, tmp_path, monkeypatch):
        """Test resolving plan path from config file."""
        monkeypatch.chdir(tmp_path)

        config = tmp_path / ".pv.toml"
        config.write_text('plan_file = "plans/project.json"\n')

        result = resolve_plan_path()
        assert result == (tmp_path / "plans" / "project.json").resolve()

    def test_falls_back_to_default(self, tmp_path, monkeypatch):
        """Test falling back to plan.json when no config exists."""
        monkeypatch.chdir(tmp_path)

        result = resolve_plan_path()
        assert result.name == "plan.json"

    def test_finds_plan_in_config_dir_without_plan_file_setting(self, tmp_path, monkeypatch):
        """Test finding plan.json in config directory when plan_file not set."""
        monkeypatch.chdir(tmp_path)

        # Create config without plan_file setting
        config = tmp_path / ".pv.toml"
        config.write_text("# empty config\n")

        # Create plan.json in same directory as config
        plan = tmp_path / "plan.json"
        plan.write_text("{}")

        result = resolve_plan_path()
        assert result == plan

    def test_monorepo_subdirectory_scenario(self, tmp_path, monkeypatch):
        """Test the typical monorepo use case: running from subdirectory."""
        # Setup monorepo structure
        root = tmp_path / "monorepo"
        root.mkdir()

        # Config at root
        config = root / "pyproject.toml"
        config.write_text('[tool.pv]\nplan_file = "plan.json"\n')

        # Plan at root
        plan = root / "plan.json"
        plan.write_text('{"meta": {}}')

        # Subdirectory where user is working
        subdir = root / "packages" / "mobile" / "src"
        subdir.mkdir(parents=True)

        # Change to subdirectory
        monkeypatch.chdir(subdir)

        result = resolve_plan_path()
        assert result == plan.resolve()


class TestMonorepoIntegration:
    """Integration tests for monorepo config resolution."""

    def test_edit_command_from_subdirectory(self, tmp_path, monkeypatch, sample_plan):
        """Test that edit commands work from subdirectory with config."""
        from argparse import Namespace
        from pathlib import Path

        from plan_view.commands.edit import cmd_done

        # Setup monorepo
        root = tmp_path / "project"
        root.mkdir()

        # Config at root
        config = root / "pyproject.toml"
        config.write_text('[tool.pv]\nplan_file = "plan.json"\n')

        # Plan at root
        plan_path = root / "plan.json"
        plan_path.write_text(json.dumps(sample_plan, indent=2))

        # Subdirectory
        subdir = root / "src" / "components"
        subdir.mkdir(parents=True)

        # Change to subdirectory
        monkeypatch.chdir(subdir)

        # Run command with default path (should resolve via config)
        args = Namespace(file=Path("plan.json"), id="0.1.2", quiet=True, dry_run=False)
        cmd_done(args)

        # Verify the plan was updated at the root location
        updated = json.loads(plan_path.read_text())
        task = None
        for phase in updated["phases"]:
            for t in phase.get("tasks", []):
                if t["id"] == "0.1.2":
                    task = t
                    break
        assert task is not None
        assert task["status"] == "completed"
