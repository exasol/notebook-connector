from __future__ import annotations

from argparse import (
    ArgumentParser,
    Namespace,
)
from pathlib import Path

import nox
import yaml

# imports all nox task provided by the toolbox
# no-qa: disables ruff error
from exasol.toolbox.nox.tasks import *  # noqa: F403

from noxconfig import PROJECT_CONFIG

# default actions to be run if nothing is explicitly specified with the -s option
nox.options.sessions = ["format:fix"]


# ---------------------------------------------------------------------------
# Database Helper
# ---------------------------------------------------------------------------


import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import (
    Any,
)

import yaml
from pydantic import (
    BaseModel,
    Field,
    JsonValue,
    validator,
)


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
FILE_NAME_PATTERN = re.compile(rf"test_(.*)\.py")


def _load_test_groups() -> list[YamlObject]:
    path = PROJECT_CONFIG.root_path / "nb_tests.yaml"
    return yaml.safe_load(path.read_text())


class JobParams(BaseModel):
    runner: str | None = Field(default=None)
    pytest_params: str | None = Field(default=None)
    backend: str | None = Field(default=None)
    require_success: bool | None = Field(default=None)
    extra_params: JsonValue | None = Field(default=None)


class Job(JobParams):
    file: str
    name: str|None = Field(default=None)

    @validator("name", always=True)
    def get_address(cls, name: str|None, values: Dict[str, Any]) -> str | None:
        filename = values.get("file")
        if (
            name is None and filename
            and (m := FILE_NAME_PATTERN.match(filename))
        ):
            return m.group(1).replace("_", " ").title()
        return name

    def inherit(self, parent: JobGroup) -> Job:
        params = parent.model_dump() | self.model_dump(exclude_none=True)
        return Job(**params)


class JobGroup(JobParams):
    jobs: tuple[Job, ...] = Field(default=())
    groups: tuple[JobGroup, ...] = Field(default=())

    def inherit(self, parent: JobGroup) -> JobGroup:
        params = parent.model_dump() | self.model_dump(exclude_none=True)
        return JobGroup(**params)


class JobList(BaseModel):
    jobs: tuple[Job, ...]


def _test_jobs(group: JobGroup, parent: JobGroup | None = None) -> Iterator[Job]:
    current = group.inherit(parent) if parent else group
    for job in current.jobs:
        yield job.inherit(current)
    for child in current.groups:
        yield from _test_jobs(child, current)


@nox.session(name="get-notebook-tests", python=False)
def get_notebook_tests(session: nox.Session) -> None:
    """
    Collect notebook tests and print in Json format.
    """
    args = _parse_nb_args(session)
    data = _load_test_groups()
    group = JobGroup.model_validate(data[args.selector])
    jobs = JobList(jobs=tuple(_test_jobs(group)))
    print(f"jobs={jobs.model_dump_json()}")


def _parse_evaluate_nb_results_args(session: nox.Session) -> Namespace:
    parser = ArgumentParser(f"nox -s {session.name} [file, ...]")
    parser.add_argument(
        "files",
        type=Path,
        nargs="*",
        help="""Evalute results of notebook tests in the specified json
        files.""",
    )
    return parser.parse_args(session.posargs)


@nox.session(name="test:notebooks:evaluate-results", python=False)
def evaluate_notebook_tests_results(session: nox.Session) -> None:
    """
    Evaluate the results of the notebook tests.
    """

    def illegal_failure(data: YamlObject) -> bool:
        require_success = data.get("require_success", True)
        outcome = data.get("outcome", "failure")
        failed = outcome != "success"
        return require_success and failed

    args = _parse_evaluate_nb_results_args(session)
    json_data = (json.loads(f.read_text()) for f in args.files)
    fails = [d for d in json_data if illegal_failure(d)]
    if fails:
        session.error(
            f"{len(fails)} mandatory tests have failed:\n\n"
            + "\n\n".join(json.dumps(d, indent=4) for d in fails)
        )


# ---------------------------------------------------------------------------
# Performance Tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# UI Tests
# ---------------------------------------------------------------------------


@nox.session(name="install:playwright-browser", python=False)
def install_playwright_browser(session: nox.Session) -> None:
    """Install browser "chromium" for UI tests with playwright."""
    session.run("playwright", "install", "chromium")
