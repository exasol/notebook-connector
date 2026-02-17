from unittest.mock import (
    MagicMock,
    call,
    patch,
)

import pytest

from exasol.nb_connector.ui import jupysql_init


def test_init_jupysql_ipython_none():
    """This test is checking if proper error is coming when IPython is not there, like in normal python only."""
    with (
        patch("exasol.nb_connector.ui.jupysql_init.get_ipython", return_value=None),
        patch("exasol.nb_connector.ui.jupysql_init.open_sqlalchemy_connection"),
    ):
        with pytest.raises(
            RuntimeError,
            match="Not running inside IPython. Magic commands will not execute.",
        ):
            jupysql_init.init_jupysql(MagicMock())


def test_init_jupysql_ipython_magics():
    """This test is checking if all magic commands are running properly when IPython is there, like in notebook."""
    mock_ipy = MagicMock()
    with patch(
        "exasol.nb_connector.ui.jupysql_init.get_ipython", return_value=mock_ipy
    ):
        with (
            patch(
                "exasol.nb_connector.ui.jupysql_init.open_sqlalchemy_connection",
                return_value="ENGINE_OBJ",
            ),
            patch(
                "exasol.nb_connector.ui.jupysql_init.get_activation_sql",
                return_value="MOCK_SQL",
            ),
        ):
            mock_config = MagicMock()
            mock_config.db_schema = "MOCK_SCHEMA"
            jupysql_init.init_jupysql(mock_config)
            assert mock_ipy.mock_calls == [
                call.run_line_magic("load_ext", "sql"),
                call.push({"engine": "ENGINE_OBJ"}),
                call.run_line_magic("sql", "engine"),
                call.run_line_magic("config", "SqlMagic.short_errors = False"),
                call.run_line_magic("sql", "OPEN SCHEMA MOCK_SCHEMA"),
                call.run_line_magic("sql", "MOCK_SQL"),
            ]
