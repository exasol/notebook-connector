import getpass
import itertools
import os
from inspect import cleandoc
from pathlib import Path
from unittest.mock import Mock

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


@pytest.mark.parametrize(
    "command, kwargs, secrets, expected_show",
    [
        (
            "docker-db",
            {},
            {},
            """
            backend: onprem
            use_itde: True
            --db-mem-size: 2
            --db-disk-size: 2
            --accelerator: none
            --db-schema: SSS
            """,
        ),
        (
            "onprem",
            {
                "--db-username": "UUU",
            },
            {
                "--db-password": "SCS_EXASOL_DB_PASSWORD",
                "--bucketfs-password": "SCS_BUCKETFS_PASSWORD",
            },
            """
            backend: onprem
            use_itde: False
            --db-host-name: localhost
            --db-port: 8563
            --db-username: UUU
            --db-password: ****
            --db-use-encryption: True
            --bucketfs-host: localhost
            --bucketfs-host-internal: localhost
            --bucketfs-port: 2580
            --bucketfs-port-internal: 2580
            --bucketfs-user: w
            --bucketfs-password: ****
            --bucketfs-name: bfsdefault
            --bucket: default
            --bucketfs-use-encryption: True
            --ssl-use-cert-validation: True
            --db-schema: SSS
            """,
        ),
        (
            "saas",
            {
                "--saas-database-name": "DB",
                "--saas-account-id": "acc",
                "--saas-url": "URL",
            },
            {"--saas-token": "SCS_EXASOL_SAAS_TOKEN"},
            """
            backend: saas
            use_itde: False
            --saas-url: URL
            --saas-account-id: acc
            --saas-database-name: DB
            --saas-token: ****
            --ssl-use-cert-validation: True
            --db-schema: SSS
            """,
        ),
    ],
)
def test_round_trip(command, kwargs, secrets, expected_show, monkeypatch, sample_scs):
    def cmd_args():
        yield from [command, scs_file, "--db-schema", "SSS"]
        yield from secrets.keys()
        yield from itertools.chain.from_iterable(kwargs.items())

    scs_file = str(sample_scs.db_file)
    for i, arg in enumerate(secrets):
        env_var = secrets[arg]
        monkeypatch.setitem(os.environ, env_var, f"secret {i+1}")
    result = CliRunner().invoke(commands.configure, cmd_args())
    assert result.exit_code == 0
    result = CliRunner().invoke(commands.show, [scs_file])
    assert cleandoc(expected_show) in result.output
