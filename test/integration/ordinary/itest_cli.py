import os
from collections.abc import Iterator
from pathlib import Path
from test.utils.integration_test_utils import sample_db_file
from urllib.parse import urlparse

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


def test_roundtrip_onprem(
    use_onprem: bool,
    scs_file_path: Path,
    exasol_config: OnpremDBConfig,
    bucketfs_config: OnpremBfsConfig,
    monkeypatch: MonkeyPatch,
    backend_aware_database_params,
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
        "--db-use-encryption",
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

    bfs_url = urlparse(bucketfs_config.url)
    if bfs_url.port:
        options += ["--bucketfs-port", str(bfs_url.port)]

    result = CliRunner().invoke(commands.configure, options)
    assert result.exit_code == 0, result.output
    result = CliRunner().invoke(commands.check, ["--connect"])
    assert result.exit_code == 0, result.output
