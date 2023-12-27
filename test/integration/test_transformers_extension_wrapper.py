from contextlib import ExitStack
from test.utils.integration_test_utils import (
    activate_languages,
    assert_connection_exists,
    assert_run_empty_udf,
    create_schema_with_reverse,
    get_script_counts,
    setup_test_configuration,
)
from typing import Callable

from _pytest.fixtures import FixtureRequest
from pyexasol import ExaConnection
from pytest_itde import config

from exasol.secret_store import Secrets
from exasol.transformers_extension_wrapper import (
    BFS_CONNECTION_KEY,
    HF_CONNECTION_KEY,
    initialize_te_extension,
)


def test_initialize_te_extension(
    request: FixtureRequest,
    connection_factory: Callable[[config.Exasol], ExaConnection],
    exasol_config: config.Exasol,
    bucketfs_config: config.BucketFs,
    secrets: Secrets,
):
    test_name: str = request.node.name
    schema = test_name
    language_alias = f"PYTHON3_TE_{test_name.upper()}"
    # Create the configuration in the secret store that would be expected
    # prior to the deployment of the Transformers Extension.
    setup_test_configuration(schema, exasol_config, bucketfs_config, secrets)
    secrets.save("HF_TOKEN", "abc")

    with ExitStack() as stack:
        pyexasol_connection = stack.enter_context(connection_factory(exasol_config))
        # Create the schema, which should also exist prior to the deployment.
        stack.enter_context(create_schema_with_reverse(pyexasol_connection, secrets))

        # Run the extension deployment.
        initialize_te_extension(secrets, language_alias=language_alias)

        activate_languages(pyexasol_connection, secrets)
        assert_run_empty_udf(language_alias, pyexasol_connection, secrets)
        script_counts = get_script_counts(pyexasol_connection, secrets)
        assert script_counts["UDF"] > 5
        assert_connection_exists(secrets.get(BFS_CONNECTION_KEY), pyexasol_connection)
        assert_connection_exists(secrets.get(HF_CONNECTION_KEY), pyexasol_connection)
