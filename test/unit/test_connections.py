import ssl
import tempfile
import types
import unittest.mock
from contextlib import ExitStack
from typing import Optional
from unittest.mock import create_autospec

import pytest

from exasol.connections import (
    get_external_host,
    open_bucketfs_connection,
    open_pyexasol_connection,
    open_sqlalchemy_connection,
)
from exasol.secret_store import Secrets


@pytest.fixture
def conf() -> Secrets:
    def mock_save(self, key: str, value: str) -> Secrets:
        self._params[key] = value
        return self

    def mock_get(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        return self._params.get(key, default_value)

    mock_conf = create_autospec(Secrets)
    mock_conf._params = {}
    mock_conf.save = types.MethodType(mock_save, mock_conf)
    mock_conf.get = types.MethodType(mock_get, mock_conf)
    mock_conf.EXTERNAL_HOST_NAME = "24.134.96.2"
    mock_conf.DB_PORT = "8888"
    mock_conf.USER = "me"
    mock_conf.PASSWORD = "let_me_in"
    mock_conf.BUCKETFS_PORT = "6666"
    mock_conf.BUCKETFS_USER = "buck_user"
    mock_conf.BUCKETFS_PASSWORD = "buck_pwd"
    mock_conf.BUCKETFS_BUCKET = "my_bucket"

    return mock_conf


def test_get_external_host(conf):
    assert get_external_host(conf) == f"{conf.EXTERNAL_HOST_NAME}:{conf.DB_PORT}"


@unittest.mock.patch("pyexasol.connect")
def test_open_pyexasol_connection(mock_connect, conf):
    conf.save("SCHEMA", "IDA")

    open_pyexasol_connection(conf)
    mock_connect.assert_called_once_with(
        dsn=get_external_host(conf), user=conf.USER, password=conf.PASSWORD, schema="IDA"
    )


@unittest.mock.patch("pyexasol.connect")
def test_open_pyexasol_connection_kwargs(mock_connect, conf):
    open_pyexasol_connection(conf, connection_timeout=3, query_timeout=10)
    mock_connect.assert_called_once_with(
        dsn=get_external_host(conf),
        user=conf.USER,
        password=conf.PASSWORD,
        connection_timeout=3,
        query_timeout=10,
    )


@unittest.mock.patch("pyexasol.connect")
def test_open_pyexasol_connection_ssl(mock_connect, conf):
    with ExitStack() as stack:
        tmp_files = [
            stack.enter_context(tempfile.NamedTemporaryFile()) for _ in range(3)
        ]
        conf.save("ENCRYPTION", "True")
        conf.save("CERTIFICATE_VALIDATION", "Yes")
        conf.save("TRUSTED_CA", tmp_files[0].name)
        conf.save("CLIENT_CERTIFICATE", tmp_files[1].name)
        conf.save("PRIVATE_KEY", tmp_files[2].name)

        open_pyexasol_connection(conf)
        mock_connect.assert_called_once_with(
            dsn=get_external_host(conf),
            user=conf.USER,
            password=conf.PASSWORD,
            encryption=True,
            websocket_sslopt={
                "cert_reqs": ssl.CERT_REQUIRED,
                "ca_certs": tmp_files[0].name,
                "certfile": tmp_files[1].name,
                "keyfile": tmp_files[2].name,
            },
        )


@unittest.mock.patch("pyexasol.connect")
def test_open_pyexasol_connection_error(mock_connect, conf):
    conf.save("ENCRYPTION", "True")
    conf.save("CERTIFICATE_VALIDATION", "Yes")
    conf.save("TRUSTED_CA", "# non % existent & file")

    with pytest.raises(ValueError):
        open_pyexasol_connection(conf)


@unittest.mock.patch("sqlalchemy.create_engine")
def test_open_sqlalchemy_connection(mock_create_engine, conf):
    conf.save("SCHEMA", "IDA")

    open_sqlalchemy_connection(conf)
    mock_create_engine.assert_called_once_with(
        f"exa+websocket://{conf.USER}:{conf.PASSWORD}@{get_external_host(conf)}/IDA"
    )


@unittest.mock.patch("sqlalchemy.create_engine")
def test_open_sqlalchemy_connection_ssl(mock_create_engine, conf):
    conf.save("ENCRYPTION", "True")
    conf.save("CERTIFICATE_VALIDATION", "False")

    open_sqlalchemy_connection(conf)
    mock_create_engine.assert_called_once_with(
        f"exa+websocket://{conf.USER}:{conf.PASSWORD}@{get_external_host(conf)}"  
        "?ENCRYPTION=Yes&SSLCertificate=SSL_VERIFY_NONE"
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_connection(mock_bfs_service, conf):
    open_bucketfs_connection(conf)
    mock_bfs_service.assert_called_once_with(
        f"http://{conf.EXTERNAL_HOST_NAME}:{conf.BUCKETFS_PORT}",
        {conf.BUCKETFS_BUCKET: {"username": conf.BUCKETFS_USER, "password": conf.BUCKETFS_PASSWORD}},
    )
