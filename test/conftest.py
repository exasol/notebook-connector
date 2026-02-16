from collections.abc import Iterator
from test.bucketfs_protocol import BucketFSProtocol
from test.package_manager import PackageManager
from test.utils.secrets import sample_db_file

import pytest

from exasol.nb_connector.secret_store import Secrets


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
        choices=["none","gzip"],
        default="gzip",
        help="Compression strategy to use for SLCs",
    )

    parser.addoption(
        "--bucketfs-protocol",
        action="store",
        type=BucketFSProtocol,
        choices=list(BucketFSProtocol),
        default="https",
        help="BucketFS Protocol to use for SLC tests",
    )


@pytest.fixture(scope="session")
def package_manager(request) -> PackageManager:
    val = request.config.getoption("--package-manager")
    return PackageManager(val)


@pytest.fixture(scope="session")
def bucketfs_protocol(request) -> BucketFSProtocol:
    val = request.config.getoption("--bucketfs-protocol")
    return BucketFSProtocol(val)
