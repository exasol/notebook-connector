from test.utils.integration_test_utils import (
    get_script_counts,
)

from exasol.nb_connector.bfs_utils import put_file
from exasol.nb_connector.cloud_storage import setup_scripts
from exasol.nb_connector.connections import (
    open_bucketfs_bucket,
    open_pyexasol_connection,
)
from exasol.nb_connector.github import (
    Project,
    retrieve_jar,
)
from exasol.nb_connector.secret_store import Secrets


def test_cloud_storage_setup_scripts(secrets: Secrets, setup_itde):
    local_jar_path = retrieve_jar(Project.CLOUD_STORAGE_EXTENSION)
    bucket = open_bucketfs_bucket(secrets)
    bfs_jar_path = put_file(bucket, local_jar_path)  # type: ignore
    udf_jar_path = bfs_jar_path.as_udf_path()
    assert udf_jar_path.startswith("/buckets/")
    with open_pyexasol_connection(secrets) as db_conn:
        setup_scripts(db_conn, secrets.db_schema, udf_jar_path)
        counts = get_script_counts(db_conn, secrets)
        assert counts["UDF"] == 3


# Implementation of test case test_saas_bucket_can_be_iterated() was wrong as
# it used the content of the secret store to access the ITDE rather than a
# SaaS database instance as indicated by the name of the test.
#
# See https://github.com/exasol/bucketfs-python/issues/259
