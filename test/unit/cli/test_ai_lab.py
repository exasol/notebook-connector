"""
Unit tests for the ai_lab CLI commands:
  - start
  - stop
  - deploy-notebooks
"""

from __future__ import annotations

import signal
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
    stop,
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
# start — foreground (no --detach)
# ---------------------------------------------------------------------------


def test_start_foreground_success(runner, notebooks_dir):
    """start runs jupyter lab in foreground when --detach is not given."""
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


def test_start_foreground_custom_port(runner, notebooks_dir):
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


def test_start_foreground_keyboard_interrupt(runner, notebooks_dir):
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


# ---------------------------------------------------------------------------
# start — detached (--detach)
# ---------------------------------------------------------------------------


def test_start_detach_writes_pid_file(runner, notebooks_dir, tmp_path):
    """--detach starts Popen and writes a PID file."""
    pid_path = tmp_path / ".ai-lab" / "jupyter.pid"

    mock_process = MagicMock()
    mock_process.pid = 12345

    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        with patch("exasol.nb_connector.cli.commands.ai_lab._check_jupyterlab"):
            with patch(
                "exasol.nb_connector.cli.commands.ai_lab._pid_file",
                return_value=pid_path,
            ):
                result = runner.invoke(
                    start,
                    [
                        "--notebook-dir",
                        str(notebooks_dir),
                        "--no-browser",
                        "--detach",
                    ],
                )

    assert result.exit_code == 0
    assert "12345" in result.output
    mock_popen.assert_called_once()
    assert pid_path.exists()
    assert pid_path.read_text().strip() == "12345"


def test_start_detach_no_browser_flag_forwarded(runner, notebooks_dir, tmp_path):
    """--no-browser is forwarded to the subprocess even in detached mode."""
    pid_path = tmp_path / ".ai-lab" / "jupyter.pid"
    mock_process = MagicMock()
    mock_process.pid = 99

    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        with patch("exasol.nb_connector.cli.commands.ai_lab._check_jupyterlab"):
            with patch(
                "exasol.nb_connector.cli.commands.ai_lab._pid_file",
                return_value=pid_path,
            ):
                result = runner.invoke(
                    start,
                    [
                        "--notebook-dir",
                        str(notebooks_dir),
                        "--no-browser",
                        "--detach",
                    ],
                )
    assert result.exit_code == 0
    called_cmd = mock_popen.call_args[0][0]
    assert "--no-browser" in called_cmd


# ---------------------------------------------------------------------------
# stop
# ---------------------------------------------------------------------------


def test_stop_success(runner, tmp_path):
    """stop reads PID file, checks process, sends SIGTERM, deletes file."""
    pid_path = tmp_path / ".ai-lab" / "jupyter.pid"
    pid_path.parent.mkdir(parents=True)
    pid_path.write_text("12345")

    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._pid_file",
        return_value=pid_path,
    ):
        with patch("exasol.nb_connector.cli.commands.ai_lab.os.kill") as mock_kill:
            result = runner.invoke(stop)

    assert result.exit_code == 0
    assert "12345" in result.output
    # First call: signal 0 (check existence)
    mock_kill.assert_any_call(12345, 0)
    # Second call: SIGTERM (graceful shutdown)
    mock_kill.assert_any_call(12345, signal.SIGTERM)
    # PID file must be deleted after stopping
    assert not pid_path.exists()


def test_stop_no_pid_file(runner, tmp_path):
    """stop exits with code 1 and error message when no PID file exists."""
    pid_path = tmp_path / ".ai-lab" / "jupyter.pid"

    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._pid_file",
        return_value=pid_path,
    ):
        result = runner.invoke(stop)

    assert result.exit_code == 1
    assert "no detached" in result.output.lower()


def test_stop_process_already_dead(runner, tmp_path):
    """stop cleans up PID file and exits with code 1 if process no longer exists."""
    pid_path = tmp_path / ".ai-lab" / "jupyter.pid"
    pid_path.parent.mkdir(parents=True)
    pid_path.write_text("99999")

    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._pid_file",
        return_value=pid_path,
    ):
        with patch("os.kill", side_effect=ProcessLookupError):
            result = runner.invoke(stop)

    assert result.exit_code == 1
    assert (
        "already stopped" in result.output.lower()
        or "not found" in result.output.lower()
    )
    # PID file must be cleaned up
    assert not pid_path.exists()


def test_stop_pid_file_corrupt(runner, tmp_path):
    """stop exits with non-zero code when PID file contains non-integer content."""
    pid_path = tmp_path / ".ai-lab" / "jupyter.pid"
    pid_path.parent.mkdir(parents=True)
    pid_path.write_text("not-a-number")

    with patch(
        "exasol.nb_connector.cli.commands.ai_lab._pid_file",
        return_value=pid_path,
    ):
        result = runner.invoke(stop)

    assert result.exit_code != 0


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
