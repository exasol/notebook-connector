from exasol.nb_connector.sagemaker_extension_wrapper import initialize_sme_extension
from exasol.nb_connector.connections import open_pyexasol_connection
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from test.utils.integration_test_utils import (
    setup_itde,
    activate_languages,
    assert_connection_exists,
    assert_run_empty_udf,
    get_script_counts,
    language_definition_context,
)


def test_initialize_sme_extension(
    secrets: Secrets,
    setup_itde
):
    # Here are fake AWS credentials. Should be fine since we are only testing
    # the deployment.
    secrets.save(CKey.sme_aws_bucket, "NoneExistent")
    secrets.save(CKey.aws_region, "neverland")
    secrets.save(CKey.aws_access_key_id, "FAKEKEYIDDONTUSEIT")
    secrets.save(CKey.aws_secret_access_key, "FakeSecretAccessKeyDontTryToUseIt")

    # At the moment the language alias is hard-coded in the extension,
    # so we have to use this exact value.
    language_alias = 'PYTHON3_SME'

    with open_pyexasol_connection(secrets) as pyexasol_connection:

        with language_definition_context(pyexasol_connection, language_alias):

            # Run the extension deployment.
            initialize_sme_extension(secrets, language_alias=language_alias)

            activate_languages(pyexasol_connection, secrets)
            assert_run_empty_udf(language_alias, pyexasol_connection, secrets)
            script_counts = get_script_counts(pyexasol_connection, secrets)
            assert script_counts["SCRIPTING"] >= 4
            assert script_counts["UDF"] >= 5
            assert_connection_exists(secrets.get(CKey.sme_aws_connection), pyexasol_connection)
