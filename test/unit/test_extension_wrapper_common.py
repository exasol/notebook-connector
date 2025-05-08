from __future__ import annotations

import re
import tempfile
import unittest.mock
from typing import Any

import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.extension_wrapper_common import (
    encapsulate_bucketfs_credentials,
)
from exasol.nb_connector.secret_store import Secrets

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


@pytest.fixture
def filled_saas_secrets(secrets) -> Secrets:
    secrets.save(CKey.saas_url, "https://mock_saas.exasol.com")
    secrets.save(CKey.saas_account_id, "faked_saas_account_id")
    secrets.save(CKey.saas_database_name, "faked_saas_database")
    secrets.save(CKey.saas_token, "faked_saas_access_token")
    secrets.save(CKey.storage_backend, "saas")
    return secrets


def validate_params(actual_params: str, expected_params: tuple[list[str], list[Any]]):
    for param_name, param_value in zip(*expected_params):
        if isinstance(param_value, str):
            param_value = f'"{param_value}"'
        elif isinstance(param_value, bool):
            param_value = str(param_value).lower()
        expected_pattern = rf'"{param_name}":\s*{param_value}'
        assert re.search(expected_pattern, actual_params) is not None


@unittest.mock.patch("pyexasol.connect")
def test_bucketfs_credentials_default(mock_connect, filled_secrets):

    path_in_bucket = "location"

    mock_connection = unittest.mock.MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connect.return_value = mock_connection

    encapsulate_bucketfs_credentials(
        filled_secrets, path_in_bucket=path_in_bucket, connection_name="whatever"
    )

    mock_connection.execute.assert_called_once()
    query_params = mock_connection.execute.call_args_list[0].kwargs["query_params"]
    validate_params(
        query_params["BUCKETFS_ADDRESS"],
        (
            ["backend", "url", "service_name", "bucket_name", "path"],
            [
                "onprem",
                f"https://{DB_HOST}:6666",
                "bfsdefault",
                "default",
                path_in_bucket,
            ],
        ),
    )
    validate_params(query_params["BUCKETFS_USER"], (["username"], ["user"]))
    validate_params(
        query_params["BUCKETFS_PASSWORD"], (["password"], ["my_bfs_password"])
    )


@unittest.mock.patch("pyexasol.connect")
def test_bucketfs_credentials_internal(mock_connect, filled_secrets):

    path_in_bucket = "location"
    internal_host = "localhost"
    internal_port = 3377
    filled_secrets.save(CKey.bfs_internal_host_name, internal_host)
    filled_secrets.save(CKey.bfs_internal_port, str(internal_port))

    mock_connection = unittest.mock.MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connect.return_value = mock_connection

    encapsulate_bucketfs_credentials(
        filled_secrets, path_in_bucket=path_in_bucket, connection_name="whatever"
    )

    mock_connection.execute.assert_called_once()
    query_params = mock_connection.execute.call_args_list[0].kwargs["query_params"]
    validate_params(
        query_params["BUCKETFS_ADDRESS"],
        (
            ["backend", "url", "service_name", "bucket_name", "path"],
            [
                "onprem",
                f"https://{internal_host}:{internal_port}",
                "bfsdefault",
                "default",
                path_in_bucket,
            ],
        ),
    )


@unittest.mock.patch("pyexasol.connect")
def test_bucketfs_credentials_verify(mock_connect, filled_secrets):

    path_in_bucket = "location"
    filled_secrets.save(CKey.cert_vld, "yes")

    mock_connection = unittest.mock.MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connect.return_value = mock_connection

    encapsulate_bucketfs_credentials(
        filled_secrets, path_in_bucket=path_in_bucket, connection_name="whatever"
    )

    mock_connection.execute.assert_called_once()
    query_params = mock_connection.execute.call_args_list[0].kwargs["query_params"]
    validate_params(query_params["BUCKETFS_ADDRESS"], (["verify"], [True]))


@unittest.mock.patch("pyexasol.connect")
def test_bucketfs_credentials_ca(mock_connect, filled_secrets):

    with tempfile.NamedTemporaryFile() as f:
        path_in_bucket = "location"
        filled_secrets.save(CKey.trusted_ca, f.name)
        filled_secrets.save(CKey.cert_vld, "yes")

        mock_connection = unittest.mock.MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connect.return_value = mock_connection

        encapsulate_bucketfs_credentials(
            filled_secrets, path_in_bucket=path_in_bucket, connection_name="whatever"
        )

        mock_connection.execute.assert_called_once()
        query_params = mock_connection.execute.call_args_list[0].kwargs["query_params"]
        validate_params(query_params["BUCKETFS_ADDRESS"], (["verify"], [False]))


@unittest.mock.patch("pyexasol.connect")
@unittest.mock.patch("exasol.saas.client.api_access.get_connection_params")
@unittest.mock.patch("exasol.saas.client.api_access.get_database_id")
def test_bucketfs_credentials_saas(
    mock_database_id, mock_connection_params, mock_connect, filled_saas_secrets
):

    path_in_bucket = "location"

    database_id = "dfdopt568se"
    mock_database_id.return_value = database_id
    mock_connection = unittest.mock.MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connect.return_value = mock_connection
    mock_connection_params.return_value = {}

    encapsulate_bucketfs_credentials(
        filled_saas_secrets, path_in_bucket=path_in_bucket, connection_name="whatever"
    )

    mock_connection.execute.assert_called_once()
    query_params = mock_connection.execute.call_args_list[0].kwargs["query_params"]
    validate_params(
        query_params["BUCKETFS_ADDRESS"],
        (
            ["backend", "url", "account_id", "path"],
            [
                "saas",
                filled_saas_secrets.get(CKey.saas_url),
                filled_saas_secrets.get(CKey.saas_account_id),
                path_in_bucket,
            ],
        ),
    )
    validate_params(query_params["BUCKETFS_USER"], (["database_id"], [database_id]))
    validate_params(
        query_params["BUCKETFS_PASSWORD"],
        (["pat"], [filled_saas_secrets.get(CKey.saas_token)]),
    )
