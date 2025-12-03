from unittest.mock import (
    MagicMock,
    patch,
)

import ipywidgets

from exasol.nb_connector.ui.access_store_ui import get_access_store_ui


def test_access_store_ui_store_read_and_write(tmp_path):
    mock_ipython = MagicMock()
    with patch(
        "exasol.nb_connector.ui.access_store_ui.get_ipython", return_value=mock_ipython
    ):
        # call UI
        ui = get_access_store_ui(str(tmp_path))
        # assert "store -r" is called
        mock_ipython.run_line_magic.assert_any_call("store", "-r")
        # find open button
        open_btn = next(
            child
            for child in ui.children
            if isinstance(child, ipywidgets.Button) and child.description == "Open"
        )
        # click open button
        mock_ipython.run_line_magic.reset_mock()
        open_btn.click()
        # assert "store" is called
        mock_ipython.run_line_magic.assert_any_call("store", "sb_store_file")
