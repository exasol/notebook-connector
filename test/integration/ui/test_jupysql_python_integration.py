import logging
import os
from pathlib import Path
import pytest
from exasol.nb_connector.ui import jupysql_init

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.jupysql_init import init_jupysql

LOG = logging.getLogger(__name__)


def test_jupysql_python_execution(tmp_path):
    config_path = tmp_path / "dummy_config_store.sqlite"
    store_password = "store_password"
    secrets = Secrets(config_path, master_password=store_password)
    secrets.save(CKey.db_schema, "SCHEMA")
    secrets.save(CKey.db_host_name, "localhost")
    secrets.save(CKey.db_port, "8563")
    secrets.save(CKey.db_user, "user")
    secrets.save(CKey.db_password, "password")
    secrets.save(CKey.storage_backend, "onprem")
    ai_lab_config = Secrets(Path(config_path), store_password)
    orig_get_ipython = jupysql_init.get_ipython
    jupysql_init.get_ipython = lambda: None
    try:
        with pytest.raises(RuntimeError, match="Not running inside IPython. Magic commands will not execute."):
            init_jupysql(ai_lab_config)
    finally:
        jupysql_init.get_ipython = orig_get_ipython
