from pathlib import Path
from test.package_manager import PackageManager

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
        "--package-manager",
        action="store",
        default="pip",
        help="Package Manager to use",
    )


@pytest.fixture(scope="session")
def package_manager(request) -> PackageManager:
    val = request.config.getoption("--package-manager")
    return PackageManager(val)
