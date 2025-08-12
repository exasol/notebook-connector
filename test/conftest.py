import contextlib
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from test.package_manager import PackageManager

import pytest
from exasol.slc.models.compression_strategy import CompressionStrategy

from exasol.nb_connector.secret_store import Secrets


@contextlib.contextmanager
def _sample_file() -> Path:
    with TemporaryDirectory() as d:
        return Path(d) / "sample_database.db"


@pytest.fixture
def secrets() -> Iterator[Secrets]:
    with _sample_file() as secret_db:
        yield Secrets(secret_db, master_password="abc")


@pytest.fixture(scope="module")
def secrets_module(sample_file_module) -> Iterator[Secrets]:
    with _sample_file() as secret_db:
        yield Secrets(sample_file_module, master_password="abc")


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
