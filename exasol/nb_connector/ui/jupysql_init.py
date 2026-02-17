# Initializing a JupySQL session
# This script is not intended to be run independently.
# It brings in the sql magic and performs common DB initialization steps,
# including opening the default schema and activating
# UDF languages at the session level.

from IPython import get_ipython

from exasol.nb_connector.connections import open_sqlalchemy_connection
from exasol.nb_connector.language_container_activation import get_activation_sql


def init_jupysql(ai_lab_config):
    open_sqlalchemy_connection(ai_lab_config)
    ipy = get_ipython()
    if ipy is None:
        raise RuntimeError(
            "Not running inside IPython. Magic commands will not execute."
        )
    ipy.run_line_magic("load_ext", "sql")
    ipy.run_line_magic("sql", "engine")
    ipy.run_line_magic("config", "SqlMagic.short_errors = False")
    ipy.run_line_magic("sql", f"OPEN SCHEMA {ai_lab_config.db_schema}")
    activation_sql = get_activation_sql(ai_lab_config)
    ipy.run_line_magic("sql", activation_sql)
