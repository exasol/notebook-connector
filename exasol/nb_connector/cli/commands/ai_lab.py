"""
CLI commands for the Exasol AI Lab Jupyter server and notebook deployment.

Usage examples
--------------
Start JupyterLab on port 8888 (default):

    ai-lab start

Start on a cutsom port:

    ai-lab start --port 9999 --ip 0.0.0.0

Deploy the bundled notebooks to a local directory:

    ai-lab deploy-notebooks --target-dir ~/notebooks-dir-name

"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

import click

from exasol.nb_connector.cli.groups import cli


def _notebook_dir():
    """Returns the path of the notebooks directory"""
    return files("exasol.nb_connector.resources").joinpath("notebooks")


def _pid_file() -> Path:
    """Returns the path of the PID file.

    The location can be overridden via the AI_LAB_PID_FILE environment variable,
    which is used in tests to avoid touching the real ~/.ai-lab/jupyter.pid.
    """
    override = os.environ.get("AI_LAB_PID_FILE")
    if override:
        return Path(override)
    return Path.home() / ".ai-lab" / "jupyter.pid"


@cli.command("start")
@click.option(
    "--port",
    default=8888,
    show_default=True,
    type=int,
    help="Port on which JupyterLab will be listening",
)
@click.option(
    "--ip",
    default="localhost",
    show_default=True,
    help="IP address JupyterLab will bind to. Use 0.0.0.0 to accept remote connections",
)
@click.option(
    "--notebook-dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory that JupyterLab will use as its root. Defaults to the notebooks embedded in the package.",
)
@click.option(
    "--no-browser",
    is_flag=True,
    default=False,
    help="Flag to prevent JupyterLab from opening in the default web browser",
)
@click.option(
    "--detach",
    is_flag=True,
    default=False,
    help="Run JupyterLab detached.",
)
def start(
    port: int, ip: str, notebook_dir: Path | None, no_browser: bool, detach: bool
) -> None:
    """Start JupyterLab server"""
    _check_jupyterlab()

    root = notebook_dir if notebook_dir else _notebook_dir()

    cmd = [
        sys.executable,
        "-m",
        "jupyter",
        "lab",
        f"--port={port}",
        f"--ip={ip}",
        f"--notebook-dir={root}",
    ]
    if no_browser:
        cmd.append("--no-browser")

    click.echo(f"Starting JupyterLab on http://{ip}:{port} (notebook dir: {root})")
    if detach:
        process = subprocess.Popen(cmd)
        pid_file = _pid_file()
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(process.pid))
        click.echo(f"JupyterLab started in detached mode, PID is {process.pid}")
        click.echo("Run 'ai-lab stop' to stop it.")
    else:
        try:
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            click.echo("\nJupyterLab stopped")


@cli.command("deploy-notebooks")
@click.option(
    "--target-dir",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory that JupyterLab will be deployed to",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Flag to overwrite existing notebooks in target directory",
)
def deploy_notebooks(target_dir: Path, overwrite: bool) -> None:
    """Deploy JupyterLab notebooks"""
    source = _notebook_dir()
    if not Path(source).is_dir():
        click.echo(
            f"Error: {source} is not a directory or directory not found", err=True
        )
        sys.exit(1)
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    skipped = 0
    for src_path in Path(source).rglob("*"):
        if src_path.is_dir():
            continue
        rel = src_path.relative_to(source)
        dst_path = target_dir / rel
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if dst_path.exists() and not overwrite:
            skipped += 1
            continue
        shutil.copy2(src_path, dst_path)
        copied += 1
    click.echo(
        f"Deployed {copied} notebooks to {target_dir}. "
        + (
            f"{skipped} notebooks skipped, use --overwrite flag to overwrite existing notebooks"
            if skipped
            else ""
        )
    )


@cli.command("stop")
def stop() -> None:
    """Stop a detached JupyterLab server"""
    pid_file = _pid_file()
    if not pid_file.exists():
        click.echo("No detached JupyterLab server found.", err=True)
        sys.exit(1)

    pid = int(pid_file.read_text().strip())
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        click.echo(f"No process found with PID {pid}. It may have already stopped")
        pid_file.unlink()
        sys.exit(1)
    os.kill(pid, signal.SIGTERM)
    pid_file.unlink()
    click.echo(f"Stopped JupyterLab server, PID is {pid}")


def _check_jupyterlab() -> None:
    """Checks whether JupyterLab is installed"""
    try:
        import jupyter_core  # noqa: F401
        import jupyterlab  # noqa: F401
    except ImportError:
        click.echo(
            "JupyterLab is not installed. "
            "Install it with:\n\n  poetry install --all-extras\n",
            err=True,
        )
        sys.exit(1)
