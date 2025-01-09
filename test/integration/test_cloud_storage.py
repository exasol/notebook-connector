import pytest
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.github import retrieve_jar, Project
from exasol.nb_connector.connections import open_bucketfs_connection, open_pyexasol_connection
from exasol.nb_connector.bfs_utils import put_file
from exasol.nb_connector.cloud_storage import setup_scripts

from test.utils.integration_test_utils import setup_itde, get_script_counts


def test_cloud_storage_setup_scripts(
    secrets: Secrets,
    setup_itde
):
    local_jar_path = retrieve_jar(Project.CLOUD_STORAGE_EXTENSION)
    bucket = open_bucketfs_connection(secrets)
    bfs_jar_path = put_file(bucket, local_jar_path)
    assert str(bfs_jar_path).startswith("/buckets/")
    with open_pyexasol_connection(secrets) as db_conn:
        setup_scripts(db_conn, secrets.db_schema, str(bfs_jar_path))
        counts = get_script_counts(db_conn, secrets)
        assert counts['UDF'] == 3


# this test was used to check SaaS integration tests, but
# might be broken if SaaSBucket will support iteration eventually
def test_saas_bucket_cannot_be_iterated(backend, secrets: Secrets, setup_itde):
    if backend != "saas":
        pytest.skip('The test runs only with SaaS database')
    bucket = open_bucketfs_connection(secrets)
    with pytest.raises(TypeError, match="not iterable"):
        list(bucket)
