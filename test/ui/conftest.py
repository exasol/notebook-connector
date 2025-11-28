from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope="session")
def solara_snapshots_directory(request: Any) -> Path:
    path = Path(request.config.rootpath) / "test" / "ui" / "snapshots"
    if not path.exists():
        path.mkdir(exist_ok=True, parents=True)
    return path

#
# class ScreenShotCheck:
#
#     def __init__(self, path, monkeypatch):
#         self._monkeypatch = monkeypatch
#         self._path = path
#
#     def assert_screenshot(self, page_session,assert_solara_snapshot):
#         self._monkeypatch.chdir(self._path)
#         page_session.wait_for_timeout(1000)
#         box_element = page_session.locator(":text('Configuration Store')").locator('..').locator('..')
#         box_element.wait_for()
#         assert_solara_snapshot(box_element.screenshot())
#
#
# @pytest.fixture
# def screenshot_check(tmp_path, monkeypatch) -> ScreenShotCheck:
#     return ScreenShotCheck(tmp_path, monkeypatch)
