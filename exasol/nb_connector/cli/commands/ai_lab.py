"""
CLI commands for the Exasol AI Lab Jupyter server and notebook deployment.

Usage examples
--------------
Start JupyterLab on port 8888 (default):

    ai-lab start

Start on a custom port and bind to all interfaces:

    ai-lab start --port 9999 --ip 0.0.0.0

Deploy (copy) the bundled notebooks to a local directory:

    ai-lab deploy-notebooks --target-dir ~/my-notebooks
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click

from exasol.nb_connector.cli.groups import cli


def _notebooks_dir() -> Path:
    """Return the path to the notebooks bundled with this package."""
    # __file__ = exasol/nb_connector/cli/commands/ai_lab.py
    # parents[2] = exasol/nb_connector/
    return Path(__file__).parents[2] / "resources" / "notebooks"


# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------


@cli.command("start")
@click.option(
    "--port",
    default=8888,
    show_default=True,
    type=int,
    help="Port on which JupyterLab will listen.",
)
@click.option(
    "--ip",
    default="localhost",
    show_default=True,
    help="IP address JupyterLab will bind to.  Use 0.0.0.0 to accept remote connections.",
)
@click.option(
    "--notebook-dir",
    default=None,
    type=click.Path(file_okay=False, path_type=Path),
    help=(
        "Directory that JupyterLab will use as its root.  "
        "Defaults to the notebooks embedded in this package."
    ),
)
@click.option(
    "--no-browser",
    is_flag=True,
    default=False,
    help="Do not open a browser window automatically.",
)
def start(port: int, ip: str, notebook_dir: Path | None, no_browser: bool) -> None:
    """Start a JupyterLab server pointing at the bundled notebooks.

    Requires JupyterLab to be installed.  Install it with:

        pip install "exasol-notebook-connector[jupyter,notebook-dependencies]"
    """
    _check_jupyterlab()

    root = notebook_dir if notebook_dir is not None else _notebooks_dir()

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

    click.echo(f"Starting JupyterLab on http://{ip}:{port}  (notebook dir: {root})")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\nJupyterLab stopped.")


# ---------------------------------------------------------------------------
# deploy-notebooks
# ---------------------------------------------------------------------------


@cli.command("deploy-notebooks")
@click.option(
    "--target-dir",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory to copy the bundled notebooks into.",
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Overwrite files that already exist in the target directory.",
)
def deploy_notebooks(target_dir: Path, overwrite: bool) -> None:
    """Copy the bundled notebooks to a local directory.

    After deployment you can start JupyterLab in that directory:

        jupyter lab --notebook-dir <target-dir>
    """
    source = _notebooks_dir()
    if not source.is_dir():
        click.echo(f"Error: bundled notebook directory not found: {source}", err=True)
        sys.exit(1)

    target_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0
    for src_path in source.rglob("*"):
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
        f"Deployed {copied} file(s) to '{target_dir}'"
        + (f" ({skipped} skipped, use --overwrite to replace them)" if skipped else "")
    )


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _check_jupyterlab() -> None:
    """Abort with a helpful message when JupyterLab is not installed."""
    try:
        import jupyter_core  # noqa: F401
        import jupyterlab  # noqa: F401
    except ImportError:
        click.echo(
            "JupyterLab is not installed.  "
            'Install it with:\n\n  pip install "exasol-notebook-connector[jupyter,notebook-dependencies]"\n',
            err=True,
        )
        sys.exit(1)
