import textwrap

import sklearn

from exasol.nb_connector.connections import open_pyexasol_connection


def sklearn_version_check(ai_lab_config):
    # make sure the local scikit-learn version
    # and the DB-SLC are compatible.

    my_version = sklearn.__version__

    # Make UDF which returns the DB sklearn version
    sql = textwrap.dedent("""
    CREATE OR REPLACE PYTHON3 SCALAR SCRIPT {schema!q}.detect_scikit_learn_version() RETURNS VARCHAR(100) AS
    import sklearn
    def run(ctx):
        return sklearn.__version__ 
    /
    """)

    with open_pyexasol_connection(ai_lab_config, compression=True) as conn:
        query_params = {"schema": ai_lab_config.db_schema}
        conn.execute(query=sql, query_params=query_params)
        result = conn.execute(
            "select {schema!q}.detect_scikit_learn_version()", query_params
        ).fetchone()
        slc_scikit_learn_version = result[0]

    if slc_scikit_learn_version != my_version:
        m = (
            f"AI Lab scikit-learn version {my_version} differs from SLC. "
            f"Please refer to ./sklearn_fix_version.ipynb to fix this issue."
        )
        raise RuntimeError(m)
