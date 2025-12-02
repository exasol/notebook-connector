from unittest.mock import (
    MagicMock,
    patch,
)

from exasol.nb_connector.ui.access_store_ui import get_access_store_ui


def test_run_line_magic_store_read_n_write_():
    """
    test to validate if the run_line_magic function calls store magic for reading and writing
    """
    mock_ipython = MagicMock()
    key = "test_key"
    with patch(
        "exasol.nb_connector.ui.access_store_ui.get_ipython", return_value=mock_ipython
    ):
        get_access_store_ui()
        # assert using assert_called_once_with
        mock_ipython.run_line_magic.assert_called_once_with("store", "-r")
        mock_ipython.run_line_magic("store", key)
        # assert using assert_called_with
        mock_ipython.run_line_magic.assert_called_with("store", key)
