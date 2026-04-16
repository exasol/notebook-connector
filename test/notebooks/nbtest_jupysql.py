import os
import textwrap

# We need to manually import all fixtures that we use, directly or indirectly,
# since the pytest won't do this for us.
from test.integration.ui.common.utils.notebook_test_utils import (
    set_log_level_for_libraries,
)

from exasol.nb_connector.secret_store import Secrets

set_log_level_for_libraries()


def test_quickstart(
    notebook_runner, monkeypatch, backend_setup, notebooks_root
) -> None:
    store_path, store_password = backend_setup
    secrets = Secrets(store_path, master_password=store_password)

    monkeypatch.setenv("EXASOL_HOST", secrets.db_host_name)
    monkeypatch.setenv("EXASOL_PORT", secrets.db_port)
    monkeypatch.setenv("EXASOL_USER", secrets.db_user)
    monkeypatch.setenv("EXASOL_PASSWORD", secrets.db_password)
    monkeypatch.setenv("EXASOL_SCHEMA", secrets.db_schema)
    monkeypatch.setenv("EXASOL_SSL_CERTIFICATE", "SSL_VERIFY_NONE")

    # load_flights_data() is defined in file flight_utils.ipynb.
    # The function accepts a list of months used as suffixes for CSV files to import.
    # The CSV files have been uploaded to cloudfront in advance.
    # The URL is defined in file flight_utils.ipynb as well.
    data_import_hack = (
        "data_selection",
        textwrap.dedent("""
            load_flights_data(ai_lab_config, ['Jan 2024'])
            load_airlines_data(ai_lab_config)
        """),
    )

    current_dir = os.getcwd()
    try:
        os.chdir(notebooks_root)
        notebook_runner("main_config.ipynb")
        os.chdir("./data")
        notebook_runner("data_flights.ipynb", hacks=[data_import_hack])
        os.chdir("../jupysql")
        notebook_runner("quickstart.ipynb")
    finally:
        os.chdir(current_dir)
