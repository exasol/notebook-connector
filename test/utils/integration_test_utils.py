import textwrap
from typing import Dict
import pytest

from pyexasol import ExaConnection

from exasol.language_container_activation import get_activation_sql
from exasol.secret_store import Secrets
from exasol.itde_manager import (
    bring_itde_up,
    take_itde_down
)
from exasol.ai_lab_config import AILabConfig
from exasol.connections import open_pyexasol_connection


@pytest.fixture
def setup_itde(secrets) -> None:
    """
    Brings up the ITDE and takes it down when the tests are completed or failed.
    Creates a schema and saves its name in the secret store.
    """

    bring_itde_up(secrets)

    schema = 'INTEGRATION_TEST'
    secrets.save(AILabConfig.db_schema.value, schema)
    with open_pyexasol_connection(secrets) as pyexasol_connection:
        pyexasol_connection.execute(f"CREATE SCHEMA {schema};")

    try:
        yield
    finally:
        take_itde_down(secrets)


def activate_languages(pyexasol_connection: ExaConnection, secrets: Secrets) -> None:
    """
    Activates languages at the current session level.
    """

    activation_sql = get_activation_sql(secrets)
    pyexasol_connection.execute(activation_sql)


def assert_run_empty_udf(
    language_alias: str, pyexasol_connection: ExaConnection, secrets: Secrets
) -> None:
    """
    Creates a tiny UDF that does nothing, just returns True. Makes sure it
    works. For this function to work, the language with the specified alias
    must be activated.
    """

    pyexasol_connection.execute(
        textwrap.dedent(
            f"""
        CREATE OR REPLACE {language_alias} SCALAR SCRIPT {secrets.SCHEMA}."TEST_UDF"()
        RETURNS BOOLEAN AS
        def run(ctx):
            return True
        /
        """
        )
    )
    result = pyexasol_connection.execute(
        f'SELECT {secrets.SCHEMA}."TEST_UDF"()'
    ).fetchall()
    assert result[0][0]


def get_script_counts(
    pyexasol_connection: ExaConnection, secrets: Secrets
) -> Dict[str, int]:
    """
    Returns numbers of installed scripts of different types.
    """

    result = pyexasol_connection.execute(
        f"""
            SELECT SCRIPT_TYPE, COUNT(*) FROM SYS.EXA_ALL_SCRIPTS
            WHERE SCRIPT_SCHEMA='{secrets.SCHEMA.upper()}' GROUP BY SCRIPT_TYPE;
        """
    ).fetchall()
    return dict(result)


def assert_connection_exists(
    connection_name: str, pyexasol_connection: ExaConnection
) -> None:
    """
    Checks that a connection object with the specified name exists.
    """

    result = pyexasol_connection.execute(
        f"""
            SELECT 1 FROM SYS.EXA_ALL_CONNECTIONS
            WHERE CONNECTION_NAME='{connection_name.upper()}';
        """
    ).fetchall()
    assert result
