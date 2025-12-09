import importlib.resources
import logging
from test.unit.ui.access_store_ui.access_store_ui_app import DEFAULT_FILE_NAME
from test.unit.ui.util import solara_app_utils as solara
from unittest.mock import (
    MagicMock,
)

import ipywidgets
import pytest
from solara.server import reload

logger = logging.getLogger("solara.server.access_store_app_test")

ACCESS_STORE_APP_SRC = (
    importlib.resources.files("test.unit.ui") / "access_store_ui/access_store_ui_app.py"
)
reload.reloader.start()

NEW_FILE_NAME = "new_file.sqlite"
TEST_PASSWORD = "password"


@pytest.fixture
def store_with_file(monkeypatch):
    def _store_with_file(filename):
        mocked_ipython = MagicMock()
        mocked_ipython.run_line_magic.side_effect = lambda magic, key: (
            filename if magic == "store" and key == "sb_store_file" else None
        )
        monkeypatch.setattr("IPython.get_ipython", lambda: mocked_ipython)
        return mocked_ipython

    return _store_with_file


def test_store_read(kernel_context, no_kernel_context, store_with_file):
    store = store_with_file(NEW_FILE_NAME)
    with solara.app_box_and_rc(ACCESS_STORE_APP_SRC, kernel_context) as (box, rc):
        text = rc.find(ipywidgets.Text)[0].widget
        text.value = store.run_line_magic("store", "sb_store_file")
        assert text.value == NEW_FILE_NAME


def test_store_write(kernel_context, no_kernel_context, store_with_file):
    store = store_with_file(DEFAULT_FILE_NAME)
    with solara.app_box_and_rc(ACCESS_STORE_APP_SRC, kernel_context) as (box, rc):
        text = rc.find(ipywidgets.Text)[0].widget
        password = rc.find(ipywidgets.Password).widget
        button = rc.find(ipywidgets.Button).widget

        assert isinstance(text, ipywidgets.Text)
        assert text.value == DEFAULT_FILE_NAME

        text.value = NEW_FILE_NAME
        password.value = TEST_PASSWORD
        assert button.icon == "pen"

        button.click()
        store.run_line_magic.assert_called_with("store", "sb_store_file")
        assert button.icon == "check"
