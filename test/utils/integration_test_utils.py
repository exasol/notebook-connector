import contextlib
import re
import textwrap
from typing import Dict

from pyexasol import ExaConnection
from pytest_itde import config

from exasol.language_container_activation import get_activation_sql
from exasol.secret_store import Secrets


def setup_test_configuration(
    schema: str,
    exasol_config: config.Exasol,
    bucketfs_config: config.BucketFs,
    secrets: Secrets,
) -> None:
    """
    Creates the configuration in the secret store corresponding to the
    test database.
    """

    url_pattern = r"\A(?P<protocol>.+?)://(?P<host>.+?):(?P<port>\d+)"
    url_parse = re.match(url_pattern, bucketfs_config.url)
    secrets.save("EXTERNAL_HOST_NAME", exasol_config.host)
    secrets.save("DB_PORT", str(exasol_config.port))
    secrets.save("USER", exasol_config.username)
    secrets.save("SCHEMA", schema)
    secrets.save("PASSWORD", exasol_config.password)
    secrets.save("BUCKETFS_HOST_NAME", url_parse.group("host"))
    secrets.save("BUCKETFS_PORT", url_parse.group("port"))
    secrets.save("BUCKETFS_USER", bucketfs_config.username)
    secrets.save("BUCKETFS_PASSWORD", bucketfs_config.password)
    secrets.save("BUCKETFS_SERVICE", "bfsdefault")
    secrets.save("BUCKETFS_BUCKET", "default")
    secrets.save("BUCKETFS_ENCRYPTION", str("https" in url_parse.group("protocol")))
    secrets.save("ENCRYPTION", "True"),
    secrets.save("CERTIFICATE_VALIDATION", "False")


@contextlib.contextmanager
def create_schema_with_reverse(pyexasol_connection: ExaConnection, secrets: Secrets):
    """
    Creates the schema in a contextualized manner. Drops this schema on exit.
    """

    try:
        pyexasol_connection.execute(f"DROP SCHEMA IF EXISTS {secrets.SCHEMA} CASCADE;")
        pyexasol_connection.execute(f"CREATE SCHEMA {secrets.SCHEMA};")
        yield
    finally:
        pyexasol_connection.execute(f"DROP SCHEMA IF EXISTS {secrets.SCHEMA} CASCADE;")


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
