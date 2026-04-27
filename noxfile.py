from argparse import ArgumentParser, Namespace
from enum import Enum
from pathlib import Path
from typing import List, Optional

import nox
import yaml
from pydantic import BaseModel

# imports all nox task provided by the toolbox
# no-qa: disables ruff error
from exasol.toolbox.nox.tasks import *  # noqa: F403

from noxconfig import PROJECT_CONFIG

# default actions to be run if nothing is explicitly specified with the -s option
nox.options.sessions = ["format:fix"]


# ---------------------------------------------------------------------------
# Database helper
# ---------------------------------------------------------------------------


@nox.session(python=False)
def start_database(session):
    session.run(
        "itde",
        "spawn-test-environment",
        "--environment-name", "test",
        "--database-port-forward", "8563",
        "--bucketfs-port-forward", "2580",
        "--db-mem-size", "8GB",
        "--nameserver", "8.8.8.8",
    )


# ---------------------------------------------------------------------------
# JupyterLab development session
# ---------------------------------------------------------------------------


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
    session.run("ai-lab", "start", *session.posargs, external=True)


# ---------------------------------------------------------------------------
# Notebook test registry (stable / unstable)
# ---------------------------------------------------------------------------


class TestStatus(Enum):
    stable = "stable"
    unstable = "unstable"


class TestClassification(Enum):
    normal = "normal"
    large = "large"
    gpu = "gpu"


class NBTestDescription(BaseModel):
    name: str
    test_file: str
    test_backend: str


class TestList(BaseModel):
    tests: List[NBTestDescription]


class TestSets(BaseModel):
    stable: TestList
    unstable: TestList
    runner: str
    additional_pytest_parameters: Optional[str] = None


class TestRepository(BaseModel):
    normal: TestSets
    large: TestSets
    gpu: TestSets


def _load_test_repository() -> TestRepository:
    yaml_file_path = PROJECT_CONFIG.root_path / "nb_tests.yaml"
    with open(yaml_file_path, "r") as f:
        return TestRepository(**yaml.safe_load(f))


def _parse_nb_args(session: nox.Session) -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--test-status", type=TestStatus, required=True,
        help="stable or unstable",
    )
    parser.add_argument(
        "--test-classification", type=TestClassification,
        default=TestClassification.normal,
        help="normal, large or gpu",
    )
    return parser.parse_args(session.posargs)


def _get_test_sets(classification: TestClassification) -> TestSets:
    repo = _load_test_repository()
    return {
        TestClassification.normal: repo.normal,
        TestClassification.large: repo.large,
        TestClassification.gpu: repo.gpu,
    }[classification]


@nox.session(name="get-notebook-tests", python=False)
def get_notebook_tests(session: nox.Session) -> None:
    """Print the notebook test list (stable or unstable) as JSON for CI matrix."""
    args = _parse_nb_args(session)
    sets = _get_test_sets(args.test_classification)
    tests = sets.stable if args.test_status == TestStatus.stable else sets.unstable
    print(tests.model_dump_json())


@nox.session(name="get-notebook-runner", python=False)
def get_notebook_runner(session: nox.Session) -> None:
    """Print the GitHub runner to use for the given test classification."""
    args = _parse_nb_args(session)
    sets = _get_test_sets(args.test_classification)
    print(sets.runner)


@nox.session(name="get-notebook-pytest-params", python=False)
def get_notebook_pytest_params(session: nox.Session) -> None:
    """Print additional pytest parameters for the given test classification."""
    args = _parse_nb_args(session)
    sets = _get_test_sets(args.test_classification)
    if sets.additional_pytest_parameters:
        print(sets.additional_pytest_parameters)


# ---------------------------------------------------------------------------
# Performance tests
# ---------------------------------------------------------------------------


def rename(file: Path, prefix: str = "", suffix: str = "") -> Path:
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
# UI tests
# ---------------------------------------------------------------------------


@nox.session(name="install:playwright-browser", python=False)
def install_playwright_browser(session: nox.Session) -> None:
    """Install browser "chromium" for UI tests with playwright."""
    session.run("playwright", "install", "chromium")
