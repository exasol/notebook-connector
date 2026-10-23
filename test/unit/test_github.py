from __future__ import annotations

import os
import pathlib
import re
from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch

from exasol.nb_connector import github

CSE_MOCK_URL = "https://github.com/some_path/exasol-cloud-storage-extension-2.7.8.jar"

MOCKED_RELEASES_RESULT = {
    "name": "Release 2.7.8",
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


@dataclass
class RequestsMocker:
    json: dict[str, Any]
    status_code: int = 200
    text: str = ""
    get_method: Mock = Mock()

    @property
    def mock_response(self) -> Mock:
        mock = Mock(
            status_code=self.status_code,
            content=b"binary data",
            text=self.text,
        )
        mock.json = Mock(return_value=self.json)
        return mock

    def mock(self, monkeypatch: MonkeyPatch) -> RequestsMocker:
        self.get_method.return_value = self.mock_response
        monkeypatch.setattr(github.requests, "get", self.get_method)
        return self


@pytest.fixture
def simulate_download_url(monkeypatch) -> RequestsMocker:
    return RequestsMocker(MOCKED_RELEASES_RESULT).mock(monkeypatch)


def test_jar_url_success(simulate_download_url) -> None:
    tag, url = github.get_latest_version_and_jar_url(
        github.Project.CLOUD_STORAGE_EXTENSION
    )
    assert (tag, url) == ("2.7.8", CSE_MOCK_URL)


@pytest.mark.parametrize(
    "requests_mocker, expected",
    [
        pytest.param(
            RequestsMocker({}, 403, "API rate limit exceeded"),
            "https://api.github.com/repos/exasol/"
            "cloud-storage-extension/releases/latest returned status code 403: API rate limit exceeded.",
            id="status_code_403",
        ),
        pytest.param(
            RequestsMocker({"name": "Release w/o tag"}),
            f'The latest release "Release w/o tag" of cloud-storage-extension has no tag.',
            id="no_tag",
        ),
        pytest.param(
            RequestsMocker({"name": "Release 1.2.3", "tag_name": "1.2.3"}),
            f'Could not find asset with suffix "1.2.3.jar" attached '
            f'to the latest release "Release 1.2.3".',
            id="no_assets",
        ),
        pytest.param(
            RequestsMocker(
                {
                    "name": "Release 1.2.3",
                    "tag_name": "1.2.3",
                    "assets": [{"name": "other.jar"}],
                }
            ),
            f'Could not find asset with suffix "1.2.3.jar" attached '
            f'to the latest release "Release 1.2.3".',
            id="no_asset_with_suffix",
        ),
    ],
)
def test_jar_url_failure(monkeypatch, requests_mocker, expected) -> None:
    requests_mocker.mock(monkeypatch)
    with pytest.raises(github.GithubReleaseError, match=re.escape(expected)):
        github.get_latest_version_and_jar_url(github.Project.CLOUD_STORAGE_EXTENSION)


def test_retrieve_jar(simulate_download_url, tmpdir, caplog):
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
    simulate_download_url.get_method.assert_called_with(
        CSE_MOCK_URL, stream=True, timeout=10
    )
