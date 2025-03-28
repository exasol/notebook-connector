import pytest
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
    language_definition_context,
)
import os

def test_download_pre_release(secrets):
    secrets.save(CKey.text_ai_pre_release_url,
                 'https://dut5tonqye28.cloudfront.net/ai_lab/text_ai/mibe_test.zip')#this should really have a better name.
    secrets.save(CKey.text_ai_zip_password, 'xyz')
    with download_pre_release(secrets) as unzipped_files:
        expected_contents = ['my_wheel\n', 'my_slc\n']
        for f_name, expected_content in zip(unzipped_files, expected_contents):
            with open(f_name) as f:
                content = f.read()
                assert content == expected_content

def test_text_ai_extension_with_container_file(
    secrets: Secrets,
    setup_itde,
    backend
):
    # this test is very slow and downloads and unpacks a 6GB file, so we only
    # execute it in the manually triggered slow tests
    if backend != "saas":
        pytest.skip('The test runs only with SaaS database')
    language_alias = f"PYTHON3_TXAIE_TEST"
    secrets.save(CKey.text_ai_pre_release_url,
                 os.environ.get('TXAIE_PRE_RELEASE_URL'))
    secrets.save(CKey.text_ai_zip_password, os.environ.get('TXAIE_PRE_RELEASE_PASSWORD'))

    with download_pre_release(secrets) as unzipped_files:
        project_wheel, container_file = unzipped_files
        try:
            with open_pyexasol_connection(secrets) as pyexasol_connection:

                with language_definition_context(pyexasol_connection, language_alias):

                    # Run the extension deployment.
                    initialize_text_ai_extension(secrets,
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
