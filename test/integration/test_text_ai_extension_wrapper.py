from test.utils.integration_test_utils import (
    activate_languages,
    assert_connection_exists,
    assert_run_empty_udf,
    setup_itde,
)

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.connections import open_pyexasol_connection
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.text_ai_extension_wrapper import initialize_text_ai_extension


def test_text_ai_extension(conf: Secrets, setup_itde):
    # this test is very slow and downloads and unpacks a 6 GB file, so we only
    # execute it in the manually triggered slow tests
    language_alias = f"PYTHON3_TXAIE_TEST"
    initialize_text_ai_extension(conf, language_alias=language_alias)
    with open_pyexasol_connection(conf) as pyexasol_connection:
        activate_languages(pyexasol_connection, conf)
        assert_run_empty_udf(language_alias, pyexasol_connection, conf)
        assert_connection_exists(
            conf.get(CKey.txaie_bfs_connection), pyexasol_connection
        )
