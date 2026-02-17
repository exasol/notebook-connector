from pathlib import Path

import pytest
from IPython.core.error import UsageError

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui import jupysql_init
from exasol.nb_connector.ui.jupysql_init import init_jupysql


def create_test_config(tmp_path, schema, user, password, cert_vld=None):
    config_path = Path(f"{tmp_path}/dummy_config_store.sqlite")
    store_password = "store_password"
    secrets = Secrets(config_path, master_password=store_password)
    secrets.save(CKey.db_schema, schema)
    secrets.save(CKey.db_host_name, "localhost")
    secrets.save(CKey.db_port, "8563")
    secrets.save(CKey.db_user, user)
    secrets.save(CKey.db_password, password)
    secrets.save(CKey.storage_backend, "onprem")
    if cert_vld is not None:
        secrets.save(CKey.cert_vld, cert_vld)
    return config_path, store_password


def test_jupysql_no_ipython(tmp_path):
    config_path, store_password = create_test_config(
        tmp_path, "MYSCHEMA", "sys", "exasol"
    )
    ai_lab_config = Secrets(Path(config_path), store_password)
    orig_get_ipython = jupysql_init.get_ipython
    jupysql_init.get_ipython = lambda: None
    try:
        with pytest.raises(
                RuntimeError,
                match="Not running inside IPython. Magic commands will not execute.",
        ):
            init_jupysql(ai_lab_config)
    finally:
        jupysql_init.get_ipython = orig_get_ipython


def test_init_jupysql(tmp_path):
    config_path, store_password = create_test_config(
        tmp_path, "MYSCHEMA", "sys", "exasol", cert_vld="False"
    )
    ai_lab_config = Secrets(config_path, store_password)
    try:
        init_jupysql(ai_lab_config)
    except Exception as e:
        pytest.fail(f"init_jupysql raised an exception: {e}")


def test_init_jupysql_invalid_credentials(tmp_path):
    config_path, store_password = create_test_config(
        tmp_path, "MYSCHEMA", "wrong_user", "wrong_password", cert_vld="False"
    )
    ai_lab_config = Secrets(config_path, store_password)
    with pytest.raises(UsageError, match="Pass a valid connection string"):
        init_jupysql(ai_lab_config)


def test_init_jupysql_missing_schema(tmp_path):
    config_path = Path(f"{tmp_path}/dummy_config_store.sqlite")
    store_password = "store_password"
    secrets = Secrets(config_path, master_password=store_password)
    # Intentionally omit db_schema
    secrets.save(CKey.db_host_name, "localhost")
    secrets.save(CKey.db_port, "8563")
    secrets.save(CKey.db_user, "sys")
    secrets.save(CKey.db_password, "exasol")
    secrets.save(CKey.storage_backend, "onprem")
    secrets.save(CKey.cert_vld, "False")
    ai_lab_config = Secrets(config_path, store_password)
    with pytest.raises(AttributeError, match='Unknown key "db_schema"'):
        init_jupysql(ai_lab_config)
