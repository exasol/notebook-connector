import os
from collections.abc import Iterator
from pathlib import Path
from test.utils.integration_test_utils import sample_db_file

import pytest
from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner

from exasol.nb_connector.cli import commands


@pytest.fixture
def scs_file_path() -> Iterator[Path]:
    with sample_db_file() as file:
        yield file


def test_roundtrip_saas(
    use_saas: bool,
    scs_file_path: Path,
    saas_host: str,
    saas_pat: str,
    saas_account_id: str,
    backend_aware_saas_database_id: str,
    monkeypatch: MonkeyPatch,
) -> None:
    if not use_saas:
        pytest.skip("This test requires an Exasol SaaS instance")

    secrets = {
        "SCS_FILE": str(scs_file_path),
        "SCS_MASTER_PASSWORD": "abc",
        "SCS_EXASOL_SAAS_TOKEN": saas_pat,
    }
    for env_var, value in secrets.items():
        monkeypatch.setitem(os.environ, env_var, value)

    scs_file = str(scs_file_path)
    result = CliRunner().invoke(
        commands.configure,
        [
            "saas",
            "--saas-url",
            saas_host,
            "--saas-account-id",
            saas_account_id,
            "--saas-database-id",
            backend_aware_saas_database_id,
            "--saas-token",  # from env
            "--db-schema",
            "SSS",
        ],
    )
    assert result.exit_code == 0
    result = CliRunner().invoke(commands.check, ["--connect"])
    assert result.exit_code == 0
