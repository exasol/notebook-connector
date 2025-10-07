import getpass
import itertools
import os
from collections.abc import Iterator
from inspect import cleandoc
from pathlib import Path
from test.utils.integration_test_utils import sample_db_file
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


def assert_success(result: click.testing.Result, message: str):
    assert result.exit_code == 0
    assert message in result.output


@pytest.mark.parametrize(
    "args",
    [
        (commands.check, []),
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
def scs_file() -> Iterator[Path]:
    with sample_db_file() as scs_file:
        yield scs_file


def test_check_ask_for_master_password(monkeypatch, scs_file):
    mock = Mock(return_value="interactive password")
    monkeypatch.setattr(getpass, "getpass", mock)
    result = CliRunner().invoke(commands.check, [str(scs_file)])
    assert mock.called
    assert_error(result, f"{scs_file} does not contain any backend")


@pytest.fixture
def scs_with_env(secrets, monkeypatch) -> Secrets:
    """
    Uses fixture `secrets` from conftest.py
    """
    monkeypatch.setitem(os.environ, "SCS_MASTER_PASSWORD", secrets._master_password)
    return secrets


@pytest.mark.parametrize(
    "backend, expected",
    [
        ("onprem", "on-premise"),
        ("saas", "SaaS"),
        ("docker-db", "Docker"),
    ],
)
def test_configure(backend, expected, scs_with_env):
    result = CliRunner().invoke(
        commands.configure,
        [backend, str(scs_with_env.db_file)],
    )
    assert result.exit_code == 0
    assert BackendSelector(scs_with_env).backend_name == expected


@pytest.mark.parametrize(
    "command, kwargs, env_opts, expected_show",
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
def test_round_trip(
    command,
    kwargs,
    env_opts,
    expected_show,
    monkeypatch,
    scs_with_env,
    pyexasol_connection_mock,
):
    def cmd_args():
        yield from [command, scs_file, "--db-schema", "SSS"]
        yield from env_opts.keys()
        yield from itertools.chain.from_iterable(kwargs.items())

    scs_file = str(scs_with_env.db_file)
    for i, arg in enumerate(env_opts):
        env_var = env_opts[arg]
        monkeypatch.setitem(os.environ, env_var, f"secret {i+1}")
    result = CliRunner().invoke(commands.configure, cmd_args())
    assert result.exit_code == 0

    result = CliRunner().invoke(commands.check, [scs_file, "--connect"])
    assert_success(result, f"Configuration is complete")
    if command == "docker-db":
        assert not pyexasol_connection_mock.called
        assert (
            "Warning: Verification of connection with ITDE is not implemented, yet."
            in result.output
        )
    else:
        assert pyexasol_connection_mock.called
    result = CliRunner().invoke(commands.show, [scs_file])
    assert cleandoc(expected_show) in result.output
