from __future__ import annotations

import ssl
import tempfile
import types
import unittest.mock
from contextlib import ExitStack
from typing import (
    Any,
)
from unittest.mock import create_autospec

import exasol.bucketfs as bfs
import pytest
from sqlalchemy.engine import make_url

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.connections import (
    get_external_host,
    open_bucketfs_bucket,
    open_bucketfs_connection,
    open_bucketfs_location,
    open_ibis_connection,
    open_pyexasol_connection,
    open_sqlalchemy_connection,
)
from exasol.nb_connector.secret_store import Secrets


@pytest.fixture
def mock_conf() -> Secrets:
    def mock_save(self, key: str, value: str) -> Secrets:
        self._params[key] = value
        return self

    def mock_get(self, key: str, default_value: str | None = None) -> str | None:
        return self._params.get(key, default_value)

    mock_conf = create_autospec(Secrets)
    mock_conf._params = {}
    mock_conf.save = types.MethodType(mock_save, mock_conf)
    mock_conf.get = types.MethodType(mock_get, mock_conf)
    return mock_conf


@pytest.fixture
def conf(mock_conf) -> Secrets:

    mock_conf.save(CKey.db_host_name, "24.134.96.2")
    mock_conf.save(CKey.db_port, "8888")
    mock_conf.save(CKey.db_user, "me")
    mock_conf.save(CKey.db_password, "let_me_in")
    mock_conf.save(CKey.bfs_port, "6666")
    mock_conf.save(CKey.bfs_user, "buck_user")
    mock_conf.save(CKey.bfs_password, "buck_pwd")
    mock_conf.save(CKey.bfs_service, "buck_svc")
    mock_conf.save(CKey.bfs_bucket, "my_bucket")

    return mock_conf


@pytest.fixture
def conf_saas(mock_conf) -> Secrets:

    mock_conf.save(CKey.saas_url, "https://mock_saas.exasol.com")
    mock_conf.save(CKey.saas_account_id, "w53lhsoifid794ms")
    mock_conf.save(CKey.saas_database_name, "my_database")
    mock_conf.save(CKey.saas_token, "xmfi58302lfj0ojf64ndk3ls")
    mock_conf.save(CKey.storage_backend, "saas")

    return mock_conf


@pytest.fixture
def saas_connection_params() -> dict[str, Any]:
    return {
        "dsn": "xyz.fake_saas.exasol.com:1234",
        "user": "fake_saas_user",
        "password": "fake_saas_password",
    }


def test_get_external_host(conf):
    assert (
        get_external_host(conf)
        == f"{conf.get(CKey.db_host_name)}:{conf.get(CKey.db_port)}"
    )


@unittest.mock.patch("pyexasol.connect")
def test_open_pyexasol_connection(mock_connect, conf):
    open_pyexasol_connection(conf)
    mock_connect.assert_called_once_with(
        dsn=get_external_host(conf),
        user=conf.get(CKey.db_user),
        password=conf.get(CKey.db_password),
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


@unittest.mock.patch("pyexasol.connect")
@unittest.mock.patch("exasol.saas.client.api_access.get_connection_params")
def test_open_pyexasol_connection_saas(
    mock_connection_params,
    mock_connect,
    conf_saas,
    saas_connection_params,
):
    mock_connection_params.return_value = saas_connection_params
    open_pyexasol_connection(conf_saas)
    mock_connect.assert_called_once_with(
        dsn=saas_connection_params["dsn"],
        user=saas_connection_params["user"],
        password=saas_connection_params["password"],
    )


@unittest.mock.patch("sqlalchemy.create_engine")
def test_open_sqlalchemy_connection(mock_create_engine, conf):
    setattr(conf, CKey.db_port.name, conf.get(CKey.db_port))
    open_sqlalchemy_connection(conf)
    mock_create_engine.assert_called_once_with(
        make_url(
            f"exa+websocket://{conf.get(CKey.db_user)}:{conf.get(CKey.db_password)}@{get_external_host(conf)}"
        )
    )


@unittest.mock.patch("sqlalchemy.create_engine")
def test_open_sqlalchemy_connection_ssl(mock_create_engine, conf):
    conf.save(CKey.db_encryption, "True")
    conf.save(CKey.cert_vld, "False")
    setattr(conf, CKey.db_port.name, conf.get(CKey.db_port))

    open_sqlalchemy_connection(conf)
    mock_create_engine.assert_called_once_with(
        make_url(
            f"exa+websocket://{conf.get(CKey.db_user)}:{conf.get(CKey.db_password)}@{get_external_host(conf)}"
            "?ENCRYPTION=Yes&SSLCertificate=SSL_VERIFY_NONE"
        )
    )


@unittest.mock.patch("sqlalchemy.create_engine")
@unittest.mock.patch("exasol.saas.client.api_access.get_connection_params")
def test_open_sqlalchemy_connection_saas(
    mock_connection_params,
    mock_create_engine,
    conf_saas,
    saas_connection_params,
):
    mock_connection_params.return_value = saas_connection_params
    open_sqlalchemy_connection(conf_saas)
    mock_create_engine.assert_called_once_with(
        make_url(
            f"exa+websocket://{saas_connection_params['user']}:"
            f"{saas_connection_params['password']}@"
            f"{saas_connection_params['dsn']}"
        )
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_bucket(mock_bfs_service, conf):
    open_bucketfs_bucket(conf)
    mock_bfs_service.assert_called_once_with(
        f"http://{conf.get(CKey.db_host_name)}:{conf.get(CKey.bfs_port)}",
        {
            conf.get(CKey.bfs_bucket): {
                "username": conf.get(CKey.bfs_user),
                "password": conf.get(CKey.bfs_password),
            }
        },
        False,
        conf.get(CKey.bfs_service),
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_bucket_https_no_verify(mock_bfs_service, conf):
    conf.save(CKey.bfs_encryption, "True")
    open_bucketfs_bucket(conf)
    mock_bfs_service.assert_called_once_with(
        f"https://{conf.get(CKey.db_host_name)}:{conf.get(CKey.bfs_port)}",
        {
            conf.get(CKey.bfs_bucket): {
                "username": conf.get(CKey.bfs_user),
                "password": conf.get(CKey.bfs_password),
            }
        },
        False,
        conf.get(CKey.bfs_service),
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_bucket_https_verify(mock_bfs_service, conf):
    conf.save(CKey.bfs_encryption, "True")
    conf.save(CKey.cert_vld, "True")
    open_bucketfs_bucket(conf)
    mock_bfs_service.assert_called_once_with(
        f"https://{conf.get(CKey.db_host_name)}:{conf.get(CKey.bfs_port)}",
        {
            conf.get(CKey.bfs_bucket): {
                "username": conf.get(CKey.bfs_user),
                "password": conf.get(CKey.bfs_password),
            }
        },
        True,
        conf.get(CKey.bfs_service),
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_bucket_trust_ca_file(mock_bfs_service, conf):
    conf.save(CKey.bfs_encryption, "True")
    conf.save(CKey.cert_vld, "True")
    with tempfile.NamedTemporaryFile() as tmp_file:
        conf.save(CKey.trusted_ca, tmp_file.name)
        open_bucketfs_bucket(conf)
        mock_bfs_service.assert_called_once_with(
            f"https://{conf.get(CKey.db_host_name)}:{conf.get(CKey.bfs_port)}",
            {
                conf.get(CKey.bfs_bucket): {
                    "username": conf.get(CKey.bfs_user),
                    "password": conf.get(CKey.bfs_password),
                }
            },
            tmp_file.name,
            conf.get(CKey.bfs_service),
        )


@unittest.mock.patch("exasol.bucketfs.SaaSBucket")
@unittest.mock.patch("exasol.saas.client.api_access.get_database_id")
def test_open_bucketfs_bucket_saas(mock_database_id, mock_saas_bucket, conf_saas):
    database_id = "dfdopt568se"
    mock_database_id.return_value = database_id
    open_bucketfs_bucket(conf_saas)
    mock_saas_bucket.assert_called_once_with(
        url=conf_saas.get(CKey.saas_url),
        account_id=conf_saas.get(CKey.saas_account_id),
        database_id=database_id,
        pat=conf_saas.get(CKey.saas_token),
    )


@unittest.mock.patch("exasol.bucketfs.path.build_path")
def test_open_bucketfs_location(mock_build_path, conf):
    open_bucketfs_location(conf)
    assert mock_build_path.called
    call_kwargs = mock_build_path.call_args.kwargs
    assert call_kwargs["backend"] == bfs.path.StorageBackend.onprem


@unittest.mock.patch("exasol.bucketfs.path.build_path")
@unittest.mock.patch("exasol.saas.client.api_access.get_database_id")
def test_open_bucketfs_location_saas(mock_database_id, mock_build_path, conf_saas):
    mock_database_id.return_value = "my_saas_db"
    open_bucketfs_location(conf_saas)
    assert mock_build_path.called
    call_kwargs = mock_build_path.call_args.kwargs
    assert call_kwargs["backend"] == bfs.path.StorageBackend.saas


@unittest.mock.patch("ibis.exasol.connect")
def test_open_ibis_connection(mock_connect, conf):
    schema = "test_schema"
    conf.save(CKey.db_schema, schema)
    open_ibis_connection(conf)
    mock_connect.assert_called_once_with(
        host=conf.get(CKey.db_host_name),
        port=int(conf.get(CKey.db_port)),
        user=conf.get(CKey.db_user),
        password=conf.get(CKey.db_password),
        schema=schema,
    )


@unittest.mock.patch("exasol.bucketfs.Service")
def test_open_bucketfs_connection_deprecated(mock_bfs_service, conf):
    with pytest.warns(
        DeprecationWarning, match="open_bucketfs_connection is deprecated"
    ):
        result = open_bucketfs_connection(conf)
        assert result
