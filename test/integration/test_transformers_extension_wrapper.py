from _pytest.fixtures import FixtureRequest

from exasol.nb_connector.connections import open_pyexasol_connection
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.transformers_extension_wrapper import initialize_te_extension
from test.utils.integration_test_utils import (
    setup_itde,
    activate_languages,
    assert_connection_exists,
    assert_run_empty_udf,
    get_script_counts
)


def test_initialize_te_extension(
    request: FixtureRequest,
    secrets: Secrets,
    setup_itde
):
    test_name: str = request.node.name
    language_alias = f"PYTHON3_TE_{test_name.upper()}"
    secrets.save(CKey.huggingface_token, "abc")

    with open_pyexasol_connection(secrets) as pyexasol_connection:

        # Run the extension deployment.
        initialize_te_extension(secrets, language_alias=language_alias)

        activate_languages(pyexasol_connection, secrets)
        assert_run_empty_udf(language_alias, pyexasol_connection, secrets)
        script_counts = get_script_counts(pyexasol_connection, secrets)
        assert script_counts["UDF"] > 5
        assert_connection_exists(secrets.get(CKey.te_bfs_connection), pyexasol_connection)
        assert_connection_exists(secrets.get(CKey.te_hf_connection), pyexasol_connection)
