import unittest.mock
import pytest
import tempfile

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.extension_wrapper_common import encapsulate_bucketfs_credentials


@pytest.fixture
def filled_secrets(secrets) -> Secrets:
    secrets.save(CKey.db_host_name, 'localhost')
    secrets.save(CKey.db_port, '8888')
    secrets.save(CKey.db_user, 'user')
    secrets.save(CKey.db_password, 'password')
    secrets.save(CKey.bfs_port, '6666')
    secrets.save(CKey.bfs_encryption, 'True')
    secrets.save(CKey.bfs_service, 'bfsdefault')
    secrets.save(CKey.bfs_bucket, 'default')
    secrets.save(CKey.bfs_user, 'user'),
    secrets.save(CKey.bfs_password, 'password')
    return secrets


@unittest.mock.patch("pyexasol.connect")
def test_bucketfs_credentials_default(mock_connect, filled_secrets):

    path_in_bucket = 'location'

    mock_connection = unittest.mock.MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connect.return_value = mock_connection

    encapsulate_bucketfs_credentials(filled_secrets, path_in_bucket=path_in_bucket,
                                     connection_name='whatever')
    expected_url = f"https://localhost:6666/default/{path_in_bucket};bfsdefault"

    mock_connection.execute.assert_called_once()
    query = mock_connection.execute.call_args_list[0].kwargs['query']
    assert f"TO '{expected_url}'" in query


@unittest.mock.patch("pyexasol.connect")
def test_bucketfs_credentials_not_verify(mock_connect, filled_secrets):

    path_in_bucket = 'location'
    filled_secrets.save(CKey.cert_vld, 'no')

    mock_connection = unittest.mock.MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connect.return_value = mock_connection

    encapsulate_bucketfs_credentials(filled_secrets, path_in_bucket=path_in_bucket,
                                     connection_name='whatever')
    expected_url = f"https://localhost:6666/default/{path_in_bucket};bfsdefault#False"

    mock_connection.execute.assert_called_once()
    query = mock_connection.execute.call_args_list[0].kwargs['query']
    assert f"TO '{expected_url}'" in query


@unittest.mock.patch("pyexasol.connect")
def test_bucketfs_credentials_ca(mock_connect, filled_secrets):

    with tempfile.NamedTemporaryFile() as f:
        path_in_bucket = 'location'
        filled_secrets.save(CKey.trusted_ca, f.name)
        filled_secrets.save(CKey.cert_vld, 'no')

        mock_connection = unittest.mock.MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connect.return_value = mock_connection

        encapsulate_bucketfs_credentials(filled_secrets, path_in_bucket=path_in_bucket,
                                         connection_name='whatever')
        expected_url = (f"https://localhost:6666/default/{path_in_bucket};bfsdefault"        
                        f"#{f.name}")

        mock_connection.execute.assert_called_once()
        query = mock_connection.execute.call_args_list[0].kwargs['query']
        assert f"TO '{expected_url}'" in query
