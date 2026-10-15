from __future__ import annotations

import unittest.mock

import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.sklearn_version_check import sklearn_version_check

DB_HOST = "1.2.3.4"


@pytest.fixture
def filled_secrets(secrets) -> Secrets:
    secrets.save(CKey.db_host_name, DB_HOST)
    secrets.save(CKey.db_port, "8888")
    secrets.save(CKey.db_user, "user")
    secrets.save(CKey.db_password, "my_db_password")
    secrets.save(CKey.bfs_port, "6666")
    secrets.save(CKey.bfs_encryption, "True")
    secrets.save(CKey.bfs_service, "bfsdefault")
    secrets.save(CKey.bfs_bucket, "default")
    secrets.save(CKey.bfs_user, "user"),
    secrets.save(CKey.bfs_password, "my_bfs_password")
    return secrets


@unittest.mock.patch("pyexasol.connect")
def test_sklearn_version_checker(mock_connect, filled_secrets):

    schema = "db-schema"
    filled_secrets.save(CKey.db_schema, schema)

    mock_connection = unittest.mock.MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connect.return_value = mock_connection

    with pytest.raises(RuntimeError) as exc_info:
        sklearn_version_check(filled_secrets)
    assert "AI Lab scikit-learn version" in str(exc_info.value)

    mock_connection.execute.assert_called()
