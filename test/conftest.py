from collections.abc import Iterator
from test.package_manager import PackageManager

import pytest
from exasol.slc.models.compression_strategy import CompressionStrategy

from exasol.nb_connector.secret_store import Secrets

from test.utils.integration_test_utils import sample_db_file


@pytest.fixture
def secrets() -> Iterator[Secrets]:
    with sample_db_file() as secret_db:
        yield Secrets(secret_db, master_password="abc")


@pytest.fixture(scope="module")
def secrets_module() -> Iterator[Secrets]:
    with sample_db_file() as secret_db:
        yield Secrets(secret_db, master_password="abc")


def pytest_addoption(parser):
    parser.addoption(
        "--package-manager",
        action="store",
        type=PackageManager,
        choices=list(PackageManager),
        default="pip",
        help="Package Manager to use",
    )

    parser.addoption(
        "--compression-strategy",
        action="store",
        type=CompressionStrategy,
        choices=list(CompressionStrategy),
        default="gzip",
        help="Compression Strategy to use",
    )


@pytest.fixture(scope="session")
def package_manager(request) -> PackageManager:
    val = request.config.getoption("--package-manager")
    return PackageManager(val)


@pytest.fixture(scope="session")
def compression_strategy(request) -> CompressionStrategy:
    val = request.config.getoption("--compression-strategy")
    return CompressionStrategy(val)
