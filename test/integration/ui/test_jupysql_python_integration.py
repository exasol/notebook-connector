import logging
import os
from pathlib import Path

import pytest

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
    os.environ["EXASOL_CONFIG_PATH"] = str(config_path)
    ai_lab_config = Secrets(Path(os.environ["EXASOL_CONFIG_PATH"]), store_password)
    try:
        init_jupysql(ai_lab_config)
    except Exception as e:
        LOG.error(f"Python execution error: {e}")
        assert False, f"Python execution failed: {e}"
    assert True
