import os
from pathlib import Path
from test.utils.integration_test_utils import sample_db_file
from typing import Iterator

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
) -> None:
    if not use_onprem:
        pytest.skip("This test requires an on-premise database")

    secrets = {
        "SCS_MASTER_PASSWORD": "abc",
        "SCS_EXASOL_DB_PASSWORD": exasol_config.password,
        "SCS_BUCKETFS_PASSWORD": bucketfs_config.password,
    }
    for env_var, value in secrets.items():
        monkeypatch.setitem(os.environ, env_var, value)

    scs_file = str(scs_file_path)
    bfs_url = bucketfs_config.url.split(":")
    result = CliRunner().invoke(
        commands.configure,
        [
            "onprem" "--db-host-name",
            exasol_config.host,
            "--db-port",
            str(exasol_config.port),
            "--db-username",
            exasol_config.username,
            "--db-password",  # from env
            "--db-use-encryption",  # TODO: verify!
            "--bucketfs-host",
            bfs_url[0],
            "--bucketfs-port",
            bfs_url[1],
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
            scs_file,
        ],
    )
    assert result.exit_code == 0
    result = CliRunner().invoke(commands.check, [scs_file])
    assert result.exit_code == 0
