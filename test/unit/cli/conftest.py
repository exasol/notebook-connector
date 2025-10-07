from unittest.mock import create_autospec

import pyexasol
import pytest

from exasol.nb_connector.cli.processing import processing


@pytest.fixture
def pyexasol_connection_mock(monkeypatch):
    mock = create_autospec(pyexasol.ExaConnection)
    monkeypatch.setattr(processing, "open_pyexasol_connection", mock)
    return mock
