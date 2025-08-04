from pathlib import Path

import pytest

from exasol.nb_connector.secret_store import Secrets


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    return tmp_path / "sample_database.db"


@pytest.fixture
def secrets(sample_file) -> Secrets:  # pylint: disable=W0621
    return Secrets(sample_file, master_password="abc")


def pytest_addoption(parser):
    parser.addoption(
        "--flavor",
        action="store",
        default="template-Exasol-all-python-3.10",
        help="Flavor to use",
    )


@pytest.fixture(scope="session")
def flavor(request) -> str:
    val = request.config.getoption("--flavor")
    return val
