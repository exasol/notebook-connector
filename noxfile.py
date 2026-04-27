from pathlib import Path

import nox

# imports all nox task provided by the toolbox
# no-qa: disables ruff error
from exasol.toolbox.nox.tasks import *  # noqa: F403

from noxconfig import PROJECT_CONFIG

# default actions to be run if nothing is explicitly specified with the -s option
nox.options.sessions = ["format:fix"]


@nox.session(python=False)
def start_database(session):
    session.run(
        "itde",
        "spawn-test-environment",
        "--environment-name",
        "test",
        "--database-port-forward",
        "8563",
        "--bucketfs-port-forward",
        "2580",
        "--db-mem-size",
        "8GB",
        "--nameserver",
        "8.8.8.8",
    )


@nox.session(name="jupyter", python=False)
def jupyter(session: nox.Session) -> None:
    """Start JupyterLab pointing at the notebooks embedded in the package.

    Usage:
        nox -s jupyter                    # default port 8888
        nox -s jupyter -- --port 9999     # custom port
        nox -s jupyter -- --ip 0.0.0.0   # bind to all interfaces
        nox -s jupyter -- --no-browser    # suppress auto-open
        nox -s jupyter -- --detach        # detach jupyter to run in background

    Extra arguments after '--' are forwarded to ai-lab start.
    """
    session.run("poetry", "install", "--all-extras", external=True)
    session.run(
        "ai-lab",
        "start",
        *session.posargs,
        external=True,
    )


def rename(file: Path, prefix: str = "", suffix: str = ""):
    name = file.with_suffix("").name
    return file.parent / f"{prefix}{name}{suffix}"


@nox.session(name="test:performance", python=False)
def performance_test(session: nox.Session) -> None:
    """Execute one or more performance tests."""
    if not session.posargs:
        session.error(f"Usage: nox -s {session.name} pytest_file.py")
    pytest_file = PROJECT_CONFIG.root_path / session.posargs[0]
    output = rename(pytest_file, "_", "-results.json")
    command = [
        "pytest",
        str(pytest_file),
        "--benchmark-sort=name",
        f"--benchmark-json={output}",
    ]
    session.run(*command)


@nox.session(name="install:playwright-browser", python=False)
def install_playwright_browser(session: nox.Session) -> None:
    """Install browser "chromium" for UI tests with playwright."""
    session.run("playwright", "install", "chromium")
