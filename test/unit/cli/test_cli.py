import os
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from exasol.nb_connector.cli import commands
from exasol.nb_connector.cli.processing.backend_selector import BackendSelector
from exasol.nb_connector.secret_store import Secrets


def assert_error(result: click.testing.Result, message: str):
    assert result.exit_code != 0
    assert message in result.output


@pytest.mark.parametrize(
    "args",
    [
        (commands.configure, ["onprem"]),
        (commands.configure, ["saas"]),
        (commands.configure, ["docker-db"]),
        (commands.show, []),
    ],
)
def test_missing_scs_file(args):
    result = CliRunner().invoke(*args)
    assert_error(result, "Error: Missing argument 'SCS_FILE'")


@pytest.fixture
def scs_file(tmp_path) -> Path:
    return tmp_path / "sample.sqlite"


@pytest.fixture
def sample_scs(scs_file, monkeypatch) -> Secrets:
    password = "sample password"
    monkeypatch.setitem(os.environ, "SCS_MASTER_PASSWORD", password)
    return Secrets(scs_file, password)


@pytest.mark.parametrize(
    "backend, expected",
    [
        ("onprem", "on-premise"),
        ("saas", "SaaS"),
        ("docker-db", "Docker"),
    ],
)
def test_configure(backend, expected, sample_scs):
    result = CliRunner().invoke(
        commands.configure,
        [backend, str(sample_scs.db_file)],
    )
    assert result.exit_code == 0
    assert BackendSelector(sample_scs).backend_name == expected
