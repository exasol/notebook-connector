"""
Integration tests for the ai_lab CLI commands.

These tests run the real `ai-lab` binary via subprocess with NO mocks or patches.
Every test touches the real filesystem and real processes.

Test classes:
  - TestDeployNotebooksIntegration : real file copy scenarios
  - TestStartStopIntegration       : real JupyterLab process (marked slow)
  - TestEdgeCases                  : boundary conditions on real data
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_SUBPROCESS_TIMEOUT = 60  # seconds — prevents CI from hanging forever


def ai_lab(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Invoke the real ai-lab entry-point via the current Python interpreter."""
    return subprocess.run(
        [sys.executable, "-m", "exasol.nb_connector.cli.main"] + list(args),
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        env=env or os.environ.copy(),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def notebooks_root() -> Path:
    """Real bundled notebooks directory shipped with the package."""
    from importlib.resources import files

    path = Path(str(files("exasol.nb_connector.resources").joinpath("notebooks")))
    assert path.is_dir(), f"Bundled notebooks not found at: {path}"
    return path


@pytest.fixture()
def isolated_pid_env(tmp_path: Path) -> dict:
    """
    Returns an env dict that overrides AI_LAB_PID_FILE to a temp location.
    This ensures tests never touch the real ~/.ai-lab/jupyter.pid and can
    run safely in parallel CI jobs.
    """
    pid_path = tmp_path / ".ai-lab" / "jupyter.pid"
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["AI_LAB_PID_FILE"] = str(pid_path)
    return env


# ---------------------------------------------------------------------------
# deploy-notebooks — real filesystem
# ---------------------------------------------------------------------------


class TestDeployNotebooksIntegration:

    def test_deploy_copies_real_notebooks(self, tmp_path, notebooks_root):
        """Real bundled notebooks are copied to the target directory."""
        target = tmp_path / "deployed"

        result = ai_lab("deploy-notebooks", "--target-dir", str(target))

        assert result.returncode == 0, result.stderr
        assert target.is_dir()
        ipynb_files = list(target.rglob("*.ipynb"))
        assert len(ipynb_files) > 0, "No .ipynb files were deployed"

    def test_deploy_count_matches_source(self, tmp_path, notebooks_root):
        """Number of deployed files equals number of files in bundled source."""
        target = tmp_path / "deployed"

        result = ai_lab("deploy-notebooks", "--target-dir", str(target))

        assert result.returncode == 0, result.stderr
        source_files = [f for f in notebooks_root.rglob("*") if f.is_file()]
        target_files = [f for f in target.rglob("*") if f.is_file()]
        assert len(target_files) == len(source_files)

    def test_deploy_preserves_subdirectory_structure(self, tmp_path, notebooks_root):
        """All non-hidden source subdirectories appear in the target."""
        target = tmp_path / "deployed"

        ai_lab("deploy-notebooks", "--target-dir", str(target))

        for src_sub in notebooks_root.iterdir():
            if src_sub.is_dir() and not src_sub.name.startswith("."):
                assert (
                    target / src_sub.name
                ).is_dir(), f"Subdirectory '{src_sub.name}' missing in deployed target"

    def test_deploy_all_file_types_copied(self, tmp_path, notebooks_root):
        """Non-.ipynb files (e.g. .py helpers) are also deployed."""
        target = tmp_path / "deployed"

        ai_lab("deploy-notebooks", "--target-dir", str(target))

        non_nb_sources = [
            f for f in notebooks_root.rglob("*") if f.is_file() and f.suffix != ".ipynb"
        ]
        for src in non_nb_sources:
            rel = src.relative_to(notebooks_root)
            assert (target / rel).exists(), f"Non-notebook file not deployed: {rel}"

    def test_deploy_creates_nested_target_dir(self, tmp_path):
        """deploy-notebooks creates deeply nested target dirs automatically."""
        target = tmp_path / "a" / "b" / "c" / "notebooks"
        assert not target.exists()

        result = ai_lab("deploy-notebooks", "--target-dir", str(target))

        assert result.returncode == 0, result.stderr
        assert target.is_dir()

    def test_deploy_output_reports_file_count(self, tmp_path):
        """Output message contains 'Deployed N file(s)' with N > 0."""
        target = tmp_path / "deployed"

        result = ai_lab("deploy-notebooks", "--target-dir", str(target))

        assert result.returncode == 0, result.stderr
        match = re.search(r"Deployed (\d+)", result.stdout)
        assert match, f"Expected 'Deployed N' in output, got: {result.stdout}"
        assert int(match.group(1)) > 0

    def test_deploy_no_overwrite_skips_existing_files(self, tmp_path):
        """Default (--no-overwrite) does not replace existing files."""
        target = tmp_path / "deployed"
        target.mkdir()
        sentinel = target / "sentinel.txt"
        sentinel.write_text("original")

        result = ai_lab("deploy-notebooks", "--target-dir", str(target))

        assert result.returncode == 0, result.stderr
        assert sentinel.read_text() == "original"

    def test_deploy_overwrite_replaces_existing_files(self, tmp_path, notebooks_root):
        """--overwrite replaces files that exist in the target."""
        target = tmp_path / "deployed"

        # First deploy
        ai_lab("deploy-notebooks", "--target-dir", str(target))

        # Corrupt one real notebook
        first_nb = next(target.rglob("*.ipynb"))
        original_content = first_nb.read_text()
        first_nb.write_text("corrupted-content")

        # Second deploy with --overwrite
        result = ai_lab("deploy-notebooks", "--target-dir", str(target), "--overwrite")

        assert result.returncode == 0, result.stderr
        assert first_nb.read_text() != "corrupted-content"
        assert first_nb.read_text() == original_content

    def test_deploy_missing_target_dir_option(self):
        """deploy-notebooks exits non-zero when --target-dir is not provided."""
        result = ai_lab("deploy-notebooks")

        assert result.returncode != 0
        combined = (result.stdout + result.stderr).lower()
        assert "target-dir" in combined, f"Expected 'target-dir' in output: {combined}"

    def test_deploy_second_run_skips_all_and_reports(self, tmp_path):
        """Running deploy twice without --overwrite skips all on the second run."""
        target = tmp_path / "deployed"
        cmd_args = ["deploy-notebooks", "--target-dir", str(target)]

        ai_lab(*cmd_args)
        result = ai_lab(*cmd_args)

        assert result.returncode == 0, result.stderr
        assert "skipped" in result.stdout.lower()

    def test_deploy_file_content_integrity(self, tmp_path, notebooks_root):
        """Deployed files have byte-for-byte identical content to source files."""
        target = tmp_path / "deployed"

        ai_lab("deploy-notebooks", "--target-dir", str(target))

        for src_file in notebooks_root.rglob("*"):
            if src_file.is_file() and not any(
                p.name.startswith(".") for p in src_file.parents
            ):
                rel = src_file.relative_to(notebooks_root)
                dst_file = target / rel
                assert dst_file.exists(), f"File missing in target: {rel}"
                assert (
                    dst_file.read_bytes() == src_file.read_bytes()
                ), f"Content mismatch for: {rel}"


# ---------------------------------------------------------------------------
# start + stop — real JupyterLab process
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestStartStopIntegration:

    def test_start_detach_and_stop(self, tmp_path, isolated_pid_env):
        """
        Real end-to-end: start --detach spawns JupyterLab, writes a real PID
        file, and ai-lab stop kills the process and removes the PID file.
        Uses AI_LAB_PID_FILE env var for test isolation (no shared state).
        """
        pid_path = Path(isolated_pid_env["AI_LAB_PID_FILE"])

        try:
            start_result = ai_lab(
                "start",
                "--detach",
                "--no-browser",
                "--notebook-dir",
                str(tmp_path),
                env=isolated_pid_env,
            )
            assert start_result.returncode == 0, start_result.stderr

            # Wait for PID file to appear (up to 10 seconds)
            for _ in range(20):
                if pid_path.exists():
                    break
                time.sleep(0.5)

            assert pid_path.exists(), "PID file was not created after start --detach"
            pid = int(pid_path.read_text().strip())
            assert pid > 0

            # Process must actually be running
            os.kill(pid, 0)

            # Stop it
            stop_result = ai_lab("stop", env=isolated_pid_env)
            assert stop_result.returncode == 0, stop_result.stderr
            assert str(pid) in stop_result.stdout

            # PID file must be deleted
            assert not pid_path.exists()

            # Poll instead of fixed sleep — wait up to 5s for process to die
            for _ in range(10):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.5)
                except ProcessLookupError:
                    break
            else:
                pytest.fail(f"Process {pid} still running after stop")

        finally:
            # Safety cleanup — kill any leaked process
            if pid_path.exists():
                try:
                    os.kill(int(pid_path.read_text().strip()), signal.SIGTERM)
                except (ProcessLookupError, ValueError):
                    pass  # already gone or invalid PID — both are fine
                pid_path.unlink(missing_ok=True)

    def test_stop_when_no_server_running(self, tmp_path, isolated_pid_env):
        """ai-lab stop exits with code 1 when no detached server is running."""
        result = ai_lab("stop", env=isolated_pid_env)

        assert result.returncode == 1
        combined = (result.stdout + result.stderr).lower()
        assert "no detached" in combined, f"Unexpected output: {combined}"

    def test_start_detach_pid_file_contains_valid_integer(
        self, tmp_path, isolated_pid_env
    ):
        """PID file written by start --detach contains a valid positive integer."""
        pid_path = Path(isolated_pid_env["AI_LAB_PID_FILE"])

        try:
            result = ai_lab(
                "start",
                "--detach",
                "--no-browser",
                "--notebook-dir",
                str(tmp_path),
                env=isolated_pid_env,
            )
            assert result.returncode == 0, result.stderr

            # Poll for PID file
            for _ in range(20):
                if pid_path.exists():
                    break
                time.sleep(0.5)

            assert pid_path.exists()
            content = pid_path.read_text().strip()
            assert content.isdigit(), f"PID file contains non-integer: {content!r}"
            assert int(content) > 0

        finally:
            if pid_path.exists():
                try:
                    os.kill(int(pid_path.read_text().strip()), signal.SIGTERM)
                except (ProcessLookupError, ValueError):
                    pass  # already gone or invalid PID — both are fine
                pid_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Edge cases — real CLI, real filesystem, no mocks
# ---------------------------------------------------------------------------


class TestEdgeCases:

    def test_start_help_shows_all_options(self):
        """start --help lists all expected options."""
        result = ai_lab("start", "--help")

        assert result.returncode == 0, result.stderr
        for option in ["--port", "--ip", "--notebook-dir", "--no-browser", "--detach"]:
            assert option in result.stdout, f"Option missing: {option}"

    def test_stop_help(self):
        """stop --help exits 0 and shows usage info."""
        result = ai_lab("stop", "--help")

        assert result.returncode == 0, result.stderr
        assert "stop" in result.stdout.lower()

    def test_deploy_notebooks_help(self):
        """deploy-notebooks --help exits 0 and lists all options."""
        result = ai_lab("deploy-notebooks", "--help")

        assert result.returncode == 0, result.stderr
        for option in ["--target-dir", "--overwrite", "--no-overwrite"]:
            assert option in result.stdout, f"Option missing: {option}"

    def test_ai_lab_help_lists_all_commands(self):
        """ai-lab --help lists start, stop and deploy-notebooks."""
        result = ai_lab("--help")

        assert result.returncode == 0, result.stderr
        for cmd in ["start", "stop", "deploy-notebooks"]:
            assert cmd in result.stdout, f"Command missing from --help: {cmd}"

    def test_start_help_shows_default_port(self):
        """Default port 8888 is visible in start --help output."""
        result = ai_lab("start", "--help")

        assert result.returncode == 0, result.stderr
        assert "8888" in result.stdout

    def test_stop_corrupt_pid_file(self, tmp_path, isolated_pid_env):
        """When the PID file contains garbage, ai-lab stop exits non-zero.
        Uses isolated env var so the real ~/.ai-lab/jupyter.pid is never touched.
        """
        pid_path = Path(isolated_pid_env["AI_LAB_PID_FILE"])
        pid_path.write_text("not-a-valid-pid")

        result = ai_lab("stop", env=isolated_pid_env)

        assert result.returncode != 0
        assert not pid_path.exists() or pid_path.read_text() == "not-a-valid-pid"
