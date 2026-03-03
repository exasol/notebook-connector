from pathlib import Path

import nbformat
import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui import jupysql_init
from exasol.nb_connector.ui.jupysql_init import init_jupysql
from test.integration.ui.utils.notebook_test_utils import print_notebook_output

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


def test_jupysql_init_as_subprocess(tmp_path, notebook_runner):
    """Test running jupysql_init.py logic as a notebook via nbclient with a real config file."""
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_code_cell(
            """
            from exasol.nb_connector.connections import open_pyexasol_connection
            sql = f'CREATE SCHEMA IF NOT EXISTS "{ai_lab_config.db_schema}"'
            with open_pyexasol_connection(ai_lab_config, compression=True) as conn:
                conn.execute(query=sql)
            """
        ),
        nbformat.v4.new_code_cell(
            """
            from exasol.nb_connector.ui.jupysql_init import init_jupysql
            init_jupysql(ai_lab_config)
            """
        ),
        nbformat.v4.new_code_cell(
            """
            %sql SELECT 1
            """
        ),
    ]
    executed_nb = notebook_runner(nb)
    print_notebook_output(executed_nb)
