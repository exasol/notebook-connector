from _pytest.fixtures import FixtureRequest
from exasol.secret_store import Secrets
from exasol.github import retrieve_jar, Project
from exasol.connections import open_bucketfs_connection, open_pyexasol_connection
from exasol.bfs_utils import put_file
from exasol.cloud_storage import setup_scripts

from test.utils.integration_test_utils import setup_itde, get_script_counts


def test_cloud_storage_setup_scripts(
    request: FixtureRequest,
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
