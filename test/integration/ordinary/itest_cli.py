import os
from collections.abc import Iterator
from pathlib import Path
from test.utils.integration_test_utils import sample_db_file
from urllib.parse import urlparse

import pyexasol
import pytest
from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner
from exasol.pytest_backend.itde import (
    OnpremBfsConfig,
    OnpremDBConfig,
)

from exasol.nb_connector.cli import commands


@pytest.fixture
def scs_file_path() -> Iterator[Path]:
    with sample_db_file() as file:
        yield file


# @pytest.fixture(scope="session", autouse=True)
# def xbackend_aware_onprem_database_async():
#     yield None
#
#
# @pytest.fixture(scope="session")
# def xexasol_config(request) -> OnpremDBConfig:
#     return OnpremDBConfig("192.168.124.221", 8563, "sys", "exasol")


def test_x1(use_onprem, backend_aware_database_params):
    if not use_onprem:
        pytest.skip("This test requires an on-premise database")
    params = backend_aware_database_params
    print(f"{params}")
    with pyexasol.connect(**params, compression=True) as conn:
        row = conn.execute("SELECT 1 FROM DUAL").fetchone()
    print(f'"SELECT 1 FROM DUAL" returned {row[0]}')


def test_roundtrip_onprem(
    use_onprem: bool,
    scs_file_path: Path,
    exasol_config: OnpremDBConfig,
    bucketfs_config: OnpremBfsConfig,
    monkeypatch: MonkeyPatch,
) -> None:
    if not use_onprem:
        pytest.skip("This test requires an on-premise database")

    print(f"DB Config: {exasol_config}")
    print(f"BFS Config: {bucketfs_config}")
    secrets = {
        "SCS_MASTER_PASSWORD": "abc",
        "SCS_EXASOL_DB_PASSWORD": exasol_config.password,
        "SCS_BUCKETFS_PASSWORD": bucketfs_config.password,
        "SCS_FILE": str(scs_file_path),
    }
    for env_var, value in secrets.items():
        monkeypatch.setitem(os.environ, env_var, value)

    options = [
        "onprem",
        "--db-host-name",
        exasol_config.host,
        "--db-port",
        str(exasol_config.port),
        "--db-username",
        exasol_config.username,
        "--db-password",  # from env
        "--db-use-encryption",  # TODO: verify!
        "--bucketfs-host",
        exasol_config.host,
        "--bucketfs-user",
        bucketfs_config.username,
        "--bucketfs-password",  # from env
        "--bucketfs-name",
        "bfsdefault",
        "--bucket",
        "default",
        "--no-bucketfs-use-encryption",
        "--no-ssl-use-cert-validation",
        "--db-schema",
        "SSS",
    ]

    # scs_file = str(scs_file_path)
    bfs_url = urlparse(bucketfs_config.url)
    # bfs_port = str(bfs_url.port) if bfs_url.port else "2580"
    if bfs_url.port:
        options += ["--bucketfs-port", str(bfs_url.port)]

    result = CliRunner().invoke(commands.configure, options)
    assert result.exit_code == 0, result.output
    result = CliRunner().invoke(commands.check, ["--connect"])
    assert result.exit_code == 0, result.output
