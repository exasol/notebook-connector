from __future__ import annotations

import contextlib
import textwrap
from collections.abc import (
    Generator,
    Iterator,
)
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pyexasol import ExaConnection

from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.connections import open_pyexasol_connection
from exasol.nb_connector.itde_manager import (
    bring_itde_up,
    take_itde_down,
)
from exasol.nb_connector.language_container_activation import get_activation_sql
from exasol.nb_connector.secret_store import Secrets


@contextlib.contextmanager
def sample_db_file() -> Iterator[Path]:
    with TemporaryDirectory() as d:
        yield Path(d) / "sample_database.db"


def _setup_itde_impl(secrets: Secrets) -> Iterator[None]:
    bring_itde_up(secrets)

    schema = "INTEGRATION_TEST"
    secrets.save(AILabConfig.db_schema, schema)
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
        CREATE OR REPLACE {language_alias} SCALAR SCRIPT {secrets.get(AILabConfig.db_schema)}."TEST_UDF"()
        RETURNS BOOLEAN AS
        def run(ctx):
            return True
        /
        """
        )
    )
    result = pyexasol_connection.execute(
        f'SELECT {secrets.get(AILabConfig.db_schema)}."TEST_UDF"()'
    ).fetchall()
    assert result[0][0]


def get_script_counts(
    pyexasol_connection: ExaConnection, secrets: Secrets
) -> dict[str, int]:
    """
    Returns numbers of installed scripts of different types.
    """

    result = pyexasol_connection.execute(
        f"""
            SELECT SCRIPT_TYPE, COUNT(*) FROM SYS.EXA_ALL_SCRIPTS
            WHERE SCRIPT_SCHEMA='{secrets[AILabConfig.db_schema].upper()}'
            GROUP BY SCRIPT_TYPE;
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


@contextmanager
def language_definition_context(
    pyexasol_connection: ExaConnection, language_alias: str | None = None
) -> Generator[None]:
    """
    A context manager that preserves the current language definitions at both
    SESSION and SYSTEM levels. Optionally creates a definition for the specified
    alias to test the ability to override an existing definition.
    """

    def alter_language_settings(alter_type: str, lang_definition: str):
        sql = f"ALTER {alter_type} SET SCRIPT_LANGUAGES='{lang_definition}';"
        pyexasol_connection.execute(sql)

    # Remember the current language settings.
    alter_types = ["SYSTEM", "SESSION"]
    sql0 = (
        f"""SELECT {', '.join(alter_type + '_VALUE' for alter_type in alter_types)} """
        "FROM SYS.EXA_PARAMETERS WHERE PARAMETER_NAME='SCRIPT_LANGUAGES';"
    )
    current_definitions = pyexasol_connection.execute(sql0).fetchall()[0]

    for alter_type in alter_types:
        # Creates a trivial language definition for the specified alias.
        if language_alias:
            lang_def = (
                "PYTHON=builtin_python R=builtin_r JAVA=builtin_java "
                f"PYTHON3=builtin_python3 {language_alias}=builtin_python3"
            )
            alter_language_settings(alter_type, lang_def)
    try:
        yield
    finally:
        # Restore language settings.
        for alter_type, lang_def in zip(alter_types, current_definitions):
            alter_language_settings(alter_type, lang_def)
