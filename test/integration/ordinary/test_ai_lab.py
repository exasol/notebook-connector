"""
Integration tests for the ai_lab CLI commands.

These tests run the real `ai-lab` binary via subprocess with NO mocks or patches.
Every test touches the real filesystem.

Test classes:
  - TestDeployNotebooksIntegration : real file copy scenarios
  - TestStartIntegration           : start JupyterLab and verify HTTP connectivity
  - TestEdgeCases                  : boundary conditions on real data
"""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_SUBPROCESS_TIMEOUT = 60  # seconds — prevents CI from hanging forever

# ---------------------------------------------------------------------------
# Port helper
# ---------------------------------------------------------------------------


def _free_port() -> int:
    """Ask the OS for a free TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


def _connect_via_http(url: str, timeout: float = 60.0, interval: float = 1.0) -> bool:
    """
    Try to connect to *url* via HTTP GET until it responds (any status code) or *timeout* elapses.
    Returns True if the server became reachable, False on timeout.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=3)  # nosec: B310
            return True
        except urllib.error.HTTPError:
            # Any HTTP error (e.g. 400, 403) still means the server is up
            return True
        except Exception:
            time.sleep(interval)
    return False


def ai_lab(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Invoke the real ai-lab entry-point via the current Python interpreter."""
    return subprocess.run(
        [sys.executable, "-m", "exasol.nb_connector.cli.main"] + list(args),
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT,
        env=env or os.environ.copy(),
    )


def _resource_files(
    root,
    relative: Path = Path(),
) -> list[Path]:
    files: list[Path] = []
    for entry in root.iterdir():
        entry_relative = relative / entry.name
        if entry.is_dir():
            files.extend(_resource_files(entry, entry_relative))
        elif entry.is_file():
            files.append(entry_relative)
    return files


def _resource_at(root, relative: Path):
    resource = root
    for part in relative.parts:
        resource = resource.joinpath(part)
    return resource


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def notebooks_root():
    """Real bundled notebooks directory shipped with the package."""
    from importlib.resources import files

    root = files("exasol.nb_connector.resources").joinpath("notebooks")
    assert root.is_dir(), f"Bundled notebooks not found at: {root}"
    return root


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
        source_files = _resource_files(notebooks_root)
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
            rel for rel in _resource_files(notebooks_root) if rel.suffix != ".ipynb"
        ]
        for rel in non_nb_sources:
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

        for rel in _resource_files(notebooks_root):
            if any(part.startswith(".") for part in rel.parts):
                continue
            src_file = _resource_at(notebooks_root, rel)
            dst_file = target / rel
            assert dst_file.exists(), f"File missing in target: {rel}"
            assert (
                dst_file.read_bytes() == src_file.read_bytes()
            ), f"Content mismatch for: {rel}"


# ---------------------------------------------------------------------------
# Start — real JupyterLab process, real HTTP connectivity
# ---------------------------------------------------------------------------


class TestStartIntegration:
    """
    Starts a real JupyterLab server via 'ai-lab start' and verifies that it is
    reachable over HTTP.  The server process is always terminated in teardown.
    """

    def test_start_server_responds_to_http(self, tmp_path):
        """
        'ai-lab start' launches JupyterLab and it responds to HTTP requests on
        the chosen port within a reasonable timeout.
        """
        port = _free_port()
        url = f"http://localhost:{port}/"

        cmd = [
            sys.executable,
            "-m",
            "exasol.nb_connector.cli.main",
            "start",
            "--port",
            str(port),
            "--no-browser",
            "--notebook-dir",
            str(tmp_path),
        ]

        proc = subprocess.Popen(  # nosec: B603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            reachable = _connect_via_http(url, timeout=60.0)
            assert reachable, (
                f"JupyterLab did not respond on {url} within 60 s.\n"
                f"stdout: {proc.stdout.read() if proc.stdout else ''}\n"
                f"stderr: {proc.stderr.read() if proc.stderr else ''}"
            )
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


# ---------------------------------------------------------------------------
# Edge cases — real CLI, real filesystem, no mocks
# ---------------------------------------------------------------------------


class TestEdgeCases:

    def test_start_help_shows_all_options(self):
        """start --help lists all expected options."""
        result = ai_lab("start", "--help")

        assert result.returncode == 0, result.stderr
        for option in ["--port", "--ip", "--notebook-dir", "--no-browser"]:
            assert option in result.stdout, f"Option missing: {option}"

    def test_deploy_notebooks_help(self):
        """deploy-notebooks --help exits 0 and lists all options."""
        result = ai_lab("deploy-notebooks", "--help")

        assert result.returncode == 0, result.stderr
        for option in ["--target-dir", "--overwrite", "--no-overwrite"]:
            assert option in result.stdout, f"Option missing: {option}"

    def test_ai_lab_help_lists_all_commands(self):
        """ai-lab --help lists start and deploy-notebooks."""
        result = ai_lab("--help")

        assert result.returncode == 0, result.stderr
        for cmd in ["start", "deploy-notebooks"]:
            assert cmd in result.stdout, f"Command missing from --help: {cmd}"
        assert "stop" not in result.stdout

    def test_start_help_shows_default_port(self):
        """Default port 8888 is visible in start --help output."""
        result = ai_lab("start", "--help")

        assert result.returncode == 0, result.stderr
        assert "8888" in result.stdout
