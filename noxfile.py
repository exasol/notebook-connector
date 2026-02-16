from pathlib import Path

import nox

# imports all nox task provided by the toolbox
# noqa: disables ruff error
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


def rename(file: Path, prefix: str="", suffix: str=""):
    name = file.with_suffix('').name
    return file.parent / f"{prefix}{name}{suffix}"


@nox.session(name="test:performance", python=False)
def performance_test(session: nox.Session) -> None:
    """ Execute one or more performance tests. """
    if not session.posargs:
        session.error(f"Usage: nox -s {session.name} pytest_file.py")
    pytest_file = PROJECT_CONFIG.root_path / session.posargs[0]
    output = rename(pytest_file, "_", "-results.json")
    command = [
        "pytest",
        pytest_file,
        "--benchmark-sort=name",
        f"--benchmark-json={output}",
    ]
    session.run(*command)
