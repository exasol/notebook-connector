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

import pytest
from _pytest.fixtures import FixtureRequest
from pyexasol import ExaConnection
from pytest_itde import config

from exasol.sagemaker_extension_wrapper import (
    AWS_CONNECTION_KEY,
    initialize_sme_extension,
)
from exasol.secret_store import Secrets


def test_initialize_sme_extension(
    request: FixtureRequest,
    connection_factory: Callable[[config.Exasol], ExaConnection],
    exasol_config: config.Exasol,
    bucketfs_config: config.BucketFs,
    secrets: Secrets,
):
    test_name: str = request.node.name
    schema = test_name
    # Create the configuration in the secret store that would be expected
    # prior to the deployment of the Sagemaker Extension.
    setup_test_configuration(schema, exasol_config, bucketfs_config, secrets)
    # Here are fake AWS credentials. Should be fine since we are only testing
    # the deployment.
    secrets.save("AWS_BUCKET", "NoneExistent")
    secrets.save("AWS_REGION", "neverland")
    secrets.save("AWS_ACCESS_KEY_ID", "FAKEKEYIDDONTUSEIT")
    secrets.save("AWS_SECRET_ACCESS_KEY", "FakeSecretAccessKeyDontTryToUseIt")

    with ExitStack() as stack:
        pyexasol_connection = stack.enter_context(connection_factory(exasol_config))
        # Create the schema, which should also exist prior to the deployment.
        stack.enter_context(create_schema_with_reverse(pyexasol_connection, secrets))

        # Run the extension deployment.
        initialize_sme_extension(secrets)

        activate_languages(pyexasol_connection, secrets)
        assert_run_empty_udf("PYTHON3_SME", pyexasol_connection, secrets)
        script_counts = get_script_counts(pyexasol_connection, secrets)
        assert script_counts["SCRIPTING"] >= 4
        assert script_counts["UDF"] >= 5
        assert_connection_exists(secrets.get(AWS_CONNECTION_KEY), pyexasol_connection)
