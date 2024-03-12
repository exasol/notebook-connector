import ssl
import tempfile
import types
import unittest.mock
from contextlib import ExitStack
from typing import Optional
from unittest.mock import create_autospec
from sqlalchemy.engine import make_url

import pytest

from exasol.nb_connector.connections import (
    get_external_host,
    open_bucketfs_connection,
    open_pyexasol_connection,
    open_sqlalchemy_connection,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey


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
    mock_conf.save(CKey.db_host_name, "24.134.96.2")
    mock_conf.save(CKey.db_port, "8888")
    mock_conf.save(CKey.db_user, "me")
    mock_conf.save(CKey.db_password, "let_me_in")
    mock_conf.save(CKey.bfs_port, "6666")
    mock_conf.save(CKey.bfs_user, "buck_user")
    mock_conf.save(CKey.bfs_password, "buck_pwd")
    mock_conf.save(CKey.bfs_bucket, "my_bucket")

    return mock_conf


def test_get_external_host(conf):
    assert get_external_host(conf) == f"{conf.get(CKey.db_host_name)}:{conf.get(CKey.db_port)}"


@unittest.mock.patch("pyexasol.connect")
def test_open_pyexasol_connection(mock_connect, conf):
    open_pyexasol_connection(conf)
    mock_connect.assert_called_once_with(
        dsn=get_external_host(conf), user=conf.get(CKey.db_user), password=conf.get(CKey.db_password)
    )


@unittest.mock.patch("pyexasol.connect")
def test_open_pyexasol_connection_kwargs(mock_connect, conf):
    open_pyexasol_connection(conf, connection_timeout=3, query_timeout=10)
    mock_connect.assert_called_once_with(
        dsn=get_external_host(conf),
        user=conf.get(CKey.db_user),
        password=conf.get(CKey.db_password),
        connection_timeout=3,
        query_timeout=10,
    )


@unittest.mock.patch("pyexasol.connect")
def test_open_pyexasol_connection_ssl(mock_connect, conf):
    with ExitStack() as stack:
        tmp_files = [
            stack.enter_context(tempfile.NamedTemporaryFile()) for _ in range(3)
        ]
        conf.save(CKey.db_encryption, "True")
        conf.save(CKey.cert_vld, "Yes")
        conf.save(CKey.trusted_ca, tmp_files[0].name)
        conf.save(CKey.client_cert, tmp_files[1].name)
        conf.save(CKey.client_key, tmp_files[2].name)

        open_pyexasol_connection(conf)
        mock_connect.assert_called_once_with(
            dsn=get_external_host(conf),
            user=conf.get(CKey.db_user),
            password=conf.get(CKey.db_password),
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
    conf.save(CKey.db_encryption, "True")
    conf.save(CKey.cert_vld, "Yes")
    conf.save(CKey.trusted_ca, "# non % existent & file")

    with pytest.raises(ValueError):
        open_pyexasol_connection(conf)


@unittest.mock.patch("sqlalchemy.create_engine")
def test_open_sqlalchemy_connection(mock_create_engine, conf):
    setattr(conf, CKey.db_port.name, conf.get(CKey.db_port))
    open_sqlalchemy_connection(conf)
    mock_create_engine.assert_called_once_with(
        make_url(f"exa+websocket://{conf.get(CKey.db_user)}:{conf.get(CKey.db_password)}@{get_external_host(conf)}")
    )


@unittest.mock.patch("sqlalchemy.create_engine")
def test_open_sqlalchemy_connection_ssl(mock_create_engine, conf):
    conf.save(CKey.db_encryption, "True")
    conf.save(CKey.cert_vld, "False")
    setattr(conf, CKey.db_port.name, conf.get(CKey.db_port))

    open_sqlalchemy_connection(conf)
    mock_create_engine.assert_called_once_with(
        make_url(f"exa+websocket://{conf.get(CKey.db_user)}:{conf.get(CKey.db_password)}@{get_external_host(conf)}"
                 "?ENCRYPTION=Yes&SSLCertificate=SSL_VERIFY_NONE")
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_connection(mock_bfs_service, conf):
    open_bucketfs_connection(conf)
    mock_bfs_service.assert_called_once_with(
        f"http://{conf.get(CKey.db_host_name)}:{conf.get(CKey.bfs_port)}",
        {
            conf.get(CKey.bfs_bucket): {
                "username": conf.get(CKey.bfs_user),
                "password": conf.get(CKey.bfs_password),
            }
        },
        False
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_connection_https_no_verify(mock_bfs_service, conf):
    conf.save(CKey.bfs_encryption, 'True')
    open_bucketfs_connection(conf)
    mock_bfs_service.assert_called_once_with(
        f"https://{conf.get(CKey.db_host_name)}:{conf.get(CKey.bfs_port)}",
        {
            conf.get(CKey.bfs_bucket): {
                "username": conf.get(CKey.bfs_user),
                "password": conf.get(CKey.bfs_password),
            }
        },
        False
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_connection_https_verify(mock_bfs_service, conf):
    conf.save(CKey.bfs_encryption, 'True')
    conf.save(CKey.cert_vld, 'True')
    open_bucketfs_connection(conf)
    mock_bfs_service.assert_called_once_with(
        f"https://{conf.get(CKey.db_host_name)}:{conf.get(CKey.bfs_port)}",
        {
            conf.get(CKey.bfs_bucket): {
                "username": conf.get(CKey.bfs_user),
                "password": conf.get(CKey.bfs_password),
            }
        },
        True
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_connection_trust_ca_file(mock_bfs_service, conf):
    conf.save(CKey.bfs_encryption, 'True')
    conf.save(CKey.cert_vld, 'True')
    with tempfile.NamedTemporaryFile() as tmp_file:
        conf.save(CKey.trusted_ca, tmp_file.name)
        open_bucketfs_connection(conf)
        mock_bfs_service.assert_called_once_with(
            f"https://{conf.get(CKey.db_host_name)}:{conf.get(CKey.bfs_port)}",
            {
                conf.get(CKey.bfs_bucket): {
                    "username": conf.get(CKey.bfs_user),
                    "password": conf.get(CKey.bfs_password),
                }
            },
            tmp_file.name
        )
