from argparse import (
    ArgumentParser,
    Namespace,
)
from enum import Enum
from pathlib import Path

import nox
import yaml

# imports all nox task provided by the toolbox
# no-qa: disables ruff error
from exasol.toolbox.nox.tasks import *  # noqa: F403
from pydantic import BaseModel

from noxconfig import PROJECT_CONFIG

# default actions to be run if nothing is explicitly specified with the -s option
nox.options.sessions = ["format:fix"]


# ---------------------------------------------------------------------------
# Database Helper
# ---------------------------------------------------------------------------


import json
import re
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    List,
    Set,
)

import yaml


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


# ---------------------------------------------------------------------------
# JupyterLab Development Session
# ---------------------------------------------------------------------------


@nox.session(name="jupyter", python=False)
def jupyter(session: nox.Session) -> None:
    """Start JupyterLab pointing at the notebooks embedded in the package.

    Usage:
        nox -s jupyter                    # default port 49494
        nox -s jupyter -- --port 9999     # custom port
        nox -s jupyter -- --ip 0.0.0.0   # bind to all interfaces
        nox -s jupyter -- --no-browser    # suppress auto-open

    Extra arguments after '--' are forwarded to ai-lab start.
    """
    session.run("poetry", "install", "--all-extras", external=True)
    session.run(
        "ai-lab",
        "start",
        *session.posargs,
        external=True,
    )


# ---------------------------------------------------------------------------
# Notebook Tests
# ---------------------------------------------------------------------------


def _parse_nb_args(session: nox.Session) -> Namespace:
    parser = ArgumentParser(f"nox -s {session.name} <selector>")
    parser.add_argument(
        "selector",
        type=str,
        help="""One of the test groups contained as
        top-level elements in file nb_tests.yaml.""",
    )
    return parser.parse_args(session.posargs)


YamlObject = dict[str, Any]
FILE_NAME_PATTERN = re.compile(f"test_(.*)\.py")


def _load_test_groups() -> list[YamlObject]:
    path = PROJECT_CONFIG.root_path / "nb_tests.yaml"
    return yaml.safe_load(path.read_text())


def _test_jobs(group, group_atts: YamlObject | None = None) -> Iterator[YamlObject]:
    def name(filename: str) -> str:
        if m := FILE_NAME_PATTERN.match(filename):
            return m.group(1).replace("_", " ").title()
        return ""

    group_atts = (group_atts or {}) | {
        k: v for k, v in group.items() if k not in ["groups", "jobs"]
    }
    for job in group.get("jobs", []):
        atts = group_atts | job
        if "name" not in atts:
            atts["name"] = name(atts["file"])
        yield atts

    for child in group.get("groups", []):
        yield from _test_jobs(child, group_atts)


@nox.session(name="get-notebook-tests", python=False)
def get_notebook_tests(session: nox.Session) -> None:
    """
    Collect notebook tests and print in Json format.
    """
    args = _parse_nb_args(session)
    data = _load_test_groups()
    m = list(_test_jobs(data[args.selector]))
    print(f"{json.dumps(m, indent=4)}")


def rename(file: Path, prefix: str = "", suffix: str = ""):
    name = file.with_suffix("").name
    return file.parent / f"{prefix}{name}{suffix}"


# ---------------------------------------------------------------------------
# Performance Tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# UI Tests
# ---------------------------------------------------------------------------


@nox.session(name="install:playwright-browser", python=False)
def install_playwright_browser(session: nox.Session) -> None:
    """Install browser "chromium" for UI tests with playwright."""
    session.run("playwright", "install", "chromium")
