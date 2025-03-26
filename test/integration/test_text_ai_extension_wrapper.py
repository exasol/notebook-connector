from exasol.nb_connector.text_ai_extension_wrapper import download_pre_release
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey


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
