from test.utils.integration_test_utils import (
    activate_languages,
    assert_connection_exists,
    assert_run_empty_udf,
    get_script_counts,
    language_definition_context,
    setup_itde,
)

import pytest
from _pytest.fixtures import FixtureRequest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.connections import open_pyexasol_connection
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.transformers_extension_wrapper import initialize_te_extension


def test_initialize_te_extension(secrets: Secrets, setup_itde):
    language_alias = f"PYTHON3_TE_TEST"
    secrets.save(CKey.huggingface_token, "abc")

    with open_pyexasol_connection(secrets) as pyexasol_connection:

        with language_definition_context(pyexasol_connection, language_alias):

            # Run the extension deployment.
            initialize_te_extension(secrets, language_alias=language_alias)

            activate_languages(pyexasol_connection, secrets)
            assert_run_empty_udf(language_alias, pyexasol_connection, secrets)
            script_counts = get_script_counts(pyexasol_connection, secrets)
            assert script_counts["UDF"] > 5
            assert_connection_exists(
                secrets[CKey.bfs_connection_name], pyexasol_connection
            )
            assert_connection_exists(
                secrets[CKey.te_hf_connection], pyexasol_connection
            )
