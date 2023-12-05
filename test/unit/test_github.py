import pytest
from unittest import mock
from exasol import github


MOCKED_RELEASES_RESULT = {
    "tag_name": "2.7.8",
    "assets": [
        {
            "name": "cloud-storage-extension-2.7.8-javadoc.jar",
            "browser_download_url": "url1",
        },
        {
            "name": "exasol-cloud-storage-extension-2.7.8.jar",
            "browser_download_url": "url2",
        }
    ]
}


@mock.patch("requests.get")
def test_get_latest_version_and_jar_url(get_mock: mock.MagicMock):
    get_mock.return_value = mock.MagicMock()
    get_mock.return_value.status_code = 200
    get_mock.return_value.json = mock.MagicMock(return_value=MOCKED_RELEASES_RESULT)
    res = github.get_latest_version_and_jar_url("cloud-storage-extension")
    assert res == ("2.7.8", "url2")
