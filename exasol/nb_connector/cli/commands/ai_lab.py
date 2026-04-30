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

import shutil
import subprocess  # nosec: B404
import sys
from importlib.resources import files
from pathlib import Path

import click

from exasol.nb_connector.cli.groups import cli


def _notebook_dir():
    """Returns the bundled notebooks resource directory."""
    return files("exasol.nb_connector.resources").joinpath("notebooks")


def _default_notebook_dir() -> Path:
    """Returns the default on-disk directory used by `ai-lab start`."""
    return Path.cwd() / "notebooks"


def _iter_resource_files(
    source,
    relative: Path = Path(),
):
    """Yield (resource, relative_path) tuples for all files in source recursively."""
    for entry in source.iterdir():
        entry_relative = relative / entry.name
        if entry.is_dir():
            yield from _iter_resource_files(entry, entry_relative)
        elif entry.is_file():
            yield entry, entry_relative


def _deploy_notebooks_to(target_dir: Path, overwrite: bool) -> tuple[int, int]:
    """
    Copy bundled notebooks to a filesystem directory.

    Works with package resources regardless of whether they come from a regular
    filesystem path or an import location like a zip archive.
    """
    source = _notebook_dir()
    if not source.is_dir():
        click.echo(
            f"Error: {source} is not a directory or directory not found", err=True
        )
        sys.exit(1)

    target_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    skipped = 0
    for src_entry, relative in _iter_resource_files(source):
        dst_path = target_dir / relative
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if dst_path.exists() and not overwrite:
            skipped += 1
            continue
        with src_entry.open("rb") as source_file, dst_path.open("wb") as target_file:
            shutil.copyfileobj(source_file, target_file)
        copied += 1
    return copied, skipped


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
    help="Directory that JupyterLab will use as its root. Defaults to './notebooks' in the current working directory.",
)
@click.option(
    "--no-browser",
    is_flag=True,
    default=False,
    help="Flag to prevent JupyterLab from opening in the default web browser",
)
def start(port: int, ip: str, notebook_dir: Path | None, no_browser: bool) -> None:
    """Start JupyterLab server"""
    _check_jupyterlab()

    if notebook_dir:
        root = notebook_dir
    else:
        root = _default_notebook_dir()
        copied, skipped = _deploy_notebooks_to(root, overwrite=False)
        click.echo(f"Prepared notebooks in {root} ({copied} copied, {skipped} skipped)")

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
    try:
        subprocess.run(cmd, check=True)  # nosec: B603
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
    copied, skipped = _deploy_notebooks_to(target_dir, overwrite)
    click.echo(
        f"Deployed {copied} notebooks to {target_dir}. "
        + (
            f"{skipped} notebooks skipped, use --overwrite flag to overwrite existing notebooks"
            if skipped
            else ""
        )
    )


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
