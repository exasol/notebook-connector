from pathlib import Path
from test.integration.ui.utils.ui_utils import assert_ui_screenshot
from typing import Any

import pytest


@pytest.fixture(scope="session")
def solara_snapshots_directory(request: Any) -> Path:
    path = Path(request.config.rootpath) / "ui_snapshots"
    if not path.exists():
        path.mkdir(exist_ok=True, parents=True)
    return path


@pytest.fixture
def ui_screenshot(page_session, assert_solara_snapshot):
    """Fixture for asserting UI screenshots.

    Returns a callable that forwards keyword args to
    ``assert_ui_screenshot``. Tests must pass at least
    ``anchor_selector`` (and usually ``parent_levels``) instead of
    relying on hard-coded defaults here, for example::

        ui_screenshot(anchor_selector=SAVE_BUTTON, parent_levels=1)
    """

    def _capture(**kwargs):
        if "wait_ms" not in kwargs:
            kwargs["wait_ms"] = 1000

        assert_ui_screenshot(
            assert_solara_snapshot,
            page_session,
            **kwargs,
        )

    return _capture
