from exasol.nb_connector.text_ai_extension_wrapper import download_pre_release
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

def test_download_pre_release(secrets):
    secrets.save(CKey.text_ai_pre_release_url,
                 'https://dut5tonqye28.cloudfront.net/ai_lab/text_ai/mibe_test.zip')
    secrets.save(CKey.text_ai_zip_password, 'xyz')
    with download_pre_release(secrets) as unzipped_files:
        expected_contents = ['my_wheel\n', 'my_slc\n']
        for f_name, expected_content in zip(unzipped_files, expected_contents):
            with open(f_name) as f:
                content = f.read()
                assert content == expected_content

def test_text_ai_extension_with_container_file(
    secrets: Secrets,
    setup_itde
):
    language_alias = f"PYTHON3_TXAIE_TEST"
    container_file = ""#todo

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
            script_counts = get_script_counts(pyexasol_connection, secrets)
            assert script_counts["UDF"] > 5
            assert_connection_exists(secrets.get(CKey.te_bfs_connection), pyexasol_connection)
            assert_connection_exists(secrets.get(CKey.te_hf_connection), pyexasol_connection)
