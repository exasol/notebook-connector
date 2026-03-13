from unittest.mock import (
    MagicMock,
    call,
)

import pytest

from exasol.nb_connector.ui.common import jupysql


def test_init_jupysql_ipython_none(monkeypatch):
    """This test is checking if proper error is coming when IPython is not there, like in normal python only."""
    monkeypatch.setattr(jupysql, "get_ipython", lambda: None)
    monkeypatch.setattr(jupysql, "open_sqlalchemy_connection", lambda *_: None)
    with pytest.raises(
        RuntimeError,
        match="Not running inside IPython. Magic commands will not execute.",
    ):
        jupysql.init(MagicMock())


def test_init_jupysql_ipython_magics(monkeypatch):
    """This test is checking if all magic commands are running properly when IPython is there, like in notebook."""
    mock_ipy = MagicMock()
    monkeypatch.setattr(jupysql, "get_ipython", lambda: mock_ipy)
    monkeypatch.setattr(jupysql, "open_sqlalchemy_connection", lambda *_: None)
    monkeypatch.setattr(jupysql, "get_activation_sql", lambda *_: "MOCK_SQL")
    mock_config = MagicMock()
    mock_config.db_schema = "MOCK_SCHEMA"
    jupysql.init(mock_config)
    expected_calls = [
        call.run_line_magic("load_ext", "sql"),
        call.run_line_magic("config", "SqlMagic.short_errors = False"),
        call.push({"engine": None}, interactive=True),
        call.run_line_magic("sql", "engine"),
        call.run_line_magic("sql", "OPEN SCHEMA MOCK_SCHEMA"),
        call.run_line_magic("sql", "MOCK_SQL"),
    ]
    assert mock_ipy.mock_calls == expected_calls
