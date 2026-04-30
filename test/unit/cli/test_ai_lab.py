"""
Unit tests for the ai_lab CLI commands:
  - start
  - deploy-notebooks
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import (
    MagicMock,
    patch,
)

import pytest
from click.testing import CliRunner

from exasol.nb_connector.cli.commands.ai_lab import (
    _notebook_dir,
    deploy_notebooks,
    start,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def runner() -> CliRunner:
    """Click test runner."""
    return CliRunner()


@pytest.fixture
def notebooks_dir(tmp_path: Path) -> Path:
    """A temporary directory that mimics the bundled notebooks structure."""
    nb_dir = tmp_path / "notebooks"
    nb_dir.mkdir()
    (nb_dir / "main_config.ipynb").write_text("{}")
    sub = nb_dir / "sklearn"
    sub.mkdir()
    (sub / "train.ipynb").write_text("{}")
    (sub / "helper.py").write_text("# helper")
    return nb_dir


# ---------------------------------------------------------------------------
# _notebook_dir
# ---------------------------------------------------------------------------


def test_notebook_dir_returns_traversable():
    """_notebook_dir() must return a Traversable pointing at the resources."""
    result = _notebook_dir()
    # The path must end with 'notebooks'
    assert str(result).endswith("notebooks")


# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------


def test_start_success(runner, notebooks_dir):
    """start runs jupyter lab in foreground with expected args."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch("exasol.nb_connector.cli.commands.ai_lab._check_jupyterlab"):
            result = runner.invoke(
                start,
                ["--notebook-dir", str(notebooks_dir), "--no-browser"],
            )
    assert result.exit_code == 0
    assert "Starting JupyterLab" in result.output
    mock_run.assert_called_once()
    called_cmd = mock_run.call_args[0][0]
    assert "lab" in called_cmd
    assert "--no-browser" in called_cmd


def test_start_custom_port_and_ip(runner, notebooks_dir):
    """--port and --ip are forwarded to the jupyter command."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch("exasol.nb_connector.cli.commands.ai_lab._check_jupyterlab"):
            result = runner.invoke(
                start,
                [
                    "--notebook-dir",
                    str(notebooks_dir),
                    "--port",
                    "9999",
                    "--ip",
                    "0.0.0.0",
                    "--no-browser",
                ],
            )
    assert result.exit_code == 0
    called_cmd = mock_run.call_args[0][0]
    assert "--port=9999" in called_cmd
    assert "--ip=0.0.0.0" in called_cmd


def test_start_keyboard_interrupt(runner, notebooks_dir):
    """Ctrl-C (KeyboardInterrupt) is caught and a clean message is shown."""
    with patch("subprocess.run", side_effect=KeyboardInterrupt):
        with patch("exasol.nb_connector.cli.commands.ai_lab._check_jupyterlab"):
            result = runner.invoke(
                start,
                ["--notebook-dir", str(notebooks_dir), "--no-browser"],
            )
    assert result.exit_code == 0
    assert "stopped" in result.output.lower()


def test_start_jupyterlab_not_installed(runner, notebooks_dir):
    """start aborts with exit code 1 when JupyterLab is not installed."""
    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._check_jupyterlab",
        side_effect=SystemExit(1),
    ):
        result = runner.invoke(
            start,
            ["--notebook-dir", str(notebooks_dir), "--no-browser"],
        )
    assert result.exit_code == 1


def test_start_without_notebook_dir_uses_notebook_dir_resource(runner, tmp_path):
    """Without --notebook-dir, start uses the bundled notebooks location."""
    default_dir = tmp_path / "bundled-notebooks"
    default_dir.mkdir()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch("exasol.nb_connector.cli.commands.ai_lab._check_jupyterlab"):
            with patch(
                "exasol.nb_connector.cli.commands.ai_lab._notebook_dir",
                return_value=default_dir,
            ) as mock_notebook_dir:
                with patch(
                    "exasol.nb_connector.cli.commands.ai_lab._deploy_notebooks_to",
                ) as mock_deploy:
                    result = runner.invoke(start, ["--no-browser"])

    assert result.exit_code == 0
    mock_notebook_dir.assert_called_once()
    mock_deploy.assert_not_called()
    called_cmd = mock_run.call_args[0][0]
    assert f"--notebook-dir={default_dir}" in called_cmd


def test_start_invalid_notebook_dir_falls_back_to_default(runner, tmp_path):
    """Invalid --notebook-dir falls back to the default bundled notebooks path."""
    default_dir = tmp_path / "bundled-notebooks"
    default_dir.mkdir()
    invalid_dir = tmp_path / "does-not-exist"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch("exasol.nb_connector.cli.commands.ai_lab._check_jupyterlab"):
            with patch(
                "exasol.nb_connector.cli.commands.ai_lab._notebook_dir",
                return_value=default_dir,
            ):
                result = runner.invoke(
                    start,
                    ["--notebook-dir", str(invalid_dir), "--no-browser"],
                )

    assert result.exit_code == 0
    called_cmd = mock_run.call_args[0][0]
    assert f"--notebook-dir={default_dir}" in called_cmd
    assert "Falling back to default directory" in result.output


def test_start_rejects_detach_option(runner):
    """--detach is no longer supported."""
    result = runner.invoke(start, ["--detach"])

    assert result.exit_code != 0
    assert "no such option" in result.output.lower()
    assert "--detach" in result.output


# ---------------------------------------------------------------------------
# deploy-notebooks
# ---------------------------------------------------------------------------


def test_deploy_notebooks_success(runner, notebooks_dir, tmp_path):
    """deploy-notebooks copies all files to target directory."""
    target = tmp_path / "output"

    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._notebook_dir",
        return_value=notebooks_dir,
    ):
        result = runner.invoke(
            deploy_notebooks,
            ["--target-dir", str(target)],
        )

    assert result.exit_code == 0
    assert "Deployed" in result.output
    # Check files were actually copied
    assert (target / "main_config.ipynb").exists()
    assert (target / "sklearn" / "train.ipynb").exists()
    assert (target / "sklearn" / "helper.py").exists()


def test_deploy_notebooks_creates_target_dir(runner, notebooks_dir, tmp_path):
    """deploy-notebooks creates the target directory if it does not exist."""
    target = tmp_path / "new" / "nested" / "dir"
    assert not target.exists()

    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._notebook_dir",
        return_value=notebooks_dir,
    ):
        result = runner.invoke(
            deploy_notebooks,
            ["--target-dir", str(target)],
        )

    assert result.exit_code == 0
    assert target.exists()


def test_deploy_notebooks_no_overwrite_by_default(runner, notebooks_dir, tmp_path):
    """Files already in target are skipped when --no-overwrite (default)."""
    target = tmp_path / "output"
    target.mkdir()
    existing_file = target / "main_config.ipynb"
    existing_file.write_text("original content")

    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._notebook_dir",
        return_value=notebooks_dir,
    ):
        result = runner.invoke(
            deploy_notebooks,
            ["--target-dir", str(target)],
        )

    assert result.exit_code == 0
    # Original content must NOT be overwritten
    assert existing_file.read_text() == "original content"
    assert "skipped" in result.output.lower()


def test_deploy_notebooks_overwrite(runner, notebooks_dir, tmp_path):
    """--overwrite replaces existing files in target directory."""
    target = tmp_path / "output"
    target.mkdir()
    existing_file = target / "main_config.ipynb"
    existing_file.write_text("original content")

    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._notebook_dir",
        return_value=notebooks_dir,
    ):
        result = runner.invoke(
            deploy_notebooks,
            ["--target-dir", str(target), "--overwrite"],
        )

    assert result.exit_code == 0
    # Content must be replaced with the source file content
    assert existing_file.read_text() == "{}"


def test_deploy_notebooks_missing_target_dir_option(runner):
    """deploy-notebooks exits with error when --target-dir is not provided."""
    result = runner.invoke(deploy_notebooks, [])
    assert result.exit_code != 0
    assert "target-dir" in result.output.lower()


def test_deploy_notebooks_source_not_found(runner, tmp_path):
    """deploy-notebooks exits with error when bundled notebooks dir is missing."""
    missing = tmp_path / "does_not_exist"
    target = tmp_path / "output"

    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._notebook_dir",
        return_value=missing,
    ):
        result = runner.invoke(
            deploy_notebooks,
            ["--target-dir", str(target)],
        )

    assert result.exit_code == 1
    assert "error" in result.output.lower() or "not found" in result.output.lower()
