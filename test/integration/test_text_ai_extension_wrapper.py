from pathlib import Path

from exasol.nb_connector.connections import open_pyexasol_connection
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.text_ai_extension_wrapper import initialize_text_ai_extension
from test.utils.integration_test_utils import (
    setup_itde,
    activate_languages,
    assert_connection_exists,
    assert_run_empty_udf,
    get_script_counts,
    language_definition_context,
)

def test_text_ai_extension_with_container_file(
    secrets: Secrets,
    setup_itde
):
    language_alias = f"PYTHON3_TXAIE_TEST"
    #container_file = Path("./../../export/exasol_text_ai_extension_container_release.tar.gz")
    with (download_pre_release(secrets) as unzipped_files):
        project_wheel, container_file = unzipped_files
        try:
            with open_pyexasol_connection(secrets) as pyexasol_connection:

                with language_definition_context(pyexasol_connection, language_alias):

                    # Run the extension deployment.
                    initialize_text_ai_extension(secrets,
                                                 container_file=container_file,
                                                 language_alias=language_alias,
                                                 run_deploy_scripts=False,
                                                 run_upload_models=False,
                    )

                    activate_languages(pyexasol_connection, secrets)
                    assert_run_empty_udf(language_alias, pyexasol_connection, secrets)
                    assert_connection_exists(secrets.get(CKey.txaie_bfs_connection), pyexasol_connection)
        finally:
            project_wheel.unlink()
            container_file.unlink()
