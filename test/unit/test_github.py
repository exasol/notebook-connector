import os
import pathlib
from unittest import mock

import pytest
import requests

from exasol.nb_connector import github

CSE_MOCK_URL = "https://github.com/some_path/exasol-cloud-storage-extension-2.7.8.jar"

MOCKED_RELEASES_RESULT = {
    "tag_name": "2.7.8",
    "assets": [
        {
            "name": "cloud-storage-extension-2.7.8-javadoc.jar",
            "browser_download_url": "should_not_be_used",
        },
        {
            "name": "exasol-cloud-storage-extension-2.7.8.jar",
            "browser_download_url": CSE_MOCK_URL,
        },
    ],
}


def mocked_requests_get(*args, **_):
    res = mock.create_autospec(requests.Response)
    res.status_code = 404
    url = args[0]
    if url.endswith("/releases/latest"):
        if github.Project.CLOUD_STORAGE_EXTENSION.value in url:
            res.status_code = 200
            res.json = mock.MagicMock(return_value=MOCKED_RELEASES_RESULT)
        elif github.Project.KAFKA_CONNECTOR_EXTENSION.value in url:
            # used to test error handling
            res.status_code = 500
    elif url == CSE_MOCK_URL:
        res.status_code = 200
        res.content = b"binary data"
    return res


@mock.patch("requests.get", side_effect=mocked_requests_get)
def test_get_latest_version_and_jar_url(_):
    res = github.get_latest_version_and_jar_url(github.Project.CLOUD_STORAGE_EXTENSION)
    assert res == ("2.7.8", CSE_MOCK_URL)

    with pytest.raises(RuntimeError, match="Error sending request"):
        github.get_latest_version_and_jar_url(github.Project.KAFKA_CONNECTOR_EXTENSION)


@mock.patch("requests.get", side_effect=mocked_requests_get)
def test_retrieve_jar(_, tmpdir, caplog):
    # need this as retrieve_jar works with current directory in some cases
    os.chdir(tmpdir)

    # fetch for the first time, local dir
    jar_path = github.retrieve_jar(github.Project.CLOUD_STORAGE_EXTENSION)
    assert jar_path.exists()
    assert jar_path.read_bytes() == b"binary data"

    # ensure file is recreated without cache
    old_ts = jar_path.lstat().st_ctime
    jar_path = github.retrieve_jar(
        github.Project.CLOUD_STORAGE_EXTENSION, use_local_cache=False
    )
    assert jar_path.exists()
    assert old_ts < jar_path.lstat().st_ctime

    # but with enabled cache, file is preserved
    caplog.set_level("INFO")
    caplog.clear()
    old_ts = jar_path.lstat().st_ctime_ns
    jar_path = github.retrieve_jar(
        github.Project.CLOUD_STORAGE_EXTENSION, use_local_cache=True
    )
    assert jar_path.lstat().st_ctime_ns == old_ts
    assert "skip downloading" in caplog.text

    # test storage path specification
    caplog.clear()
    stg_path = pathlib.Path(tmpdir.mkdir("sub"))
    jar_path_sub = github.retrieve_jar(
        github.Project.CLOUD_STORAGE_EXTENSION,
        use_local_cache=True,
        storage_path=stg_path,
    )
    assert jar_path_sub.exists()
    assert jar_path != jar_path_sub
    assert "Fetching jar" in caplog.text
