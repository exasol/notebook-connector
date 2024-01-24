from unittest import mock
from exasol.cloud_storage import setup_scripts


def test_setup_scripts(secrets):
    mock_db_conn = mock.MagicMock()
    mock_db_conn.execute = mock.MagicMock()
    setup_scripts(mock_db_conn, "SCHEMA", "/bucketfs/file.jar")
    assert mock_db_conn.execute.call_count == 4
    assert "OPEN SCHEMA" in mock_db_conn.execute.mock_calls[0].args[0]
    assert "CREATE OR REPLACE JAVA SET SCRIPT IMPORT_PATH" in mock_db_conn.execute.mock_calls[1].args[0]
    assert "com.exasol.cloudetl.scriptclasses.FilesImportQueryGenerator" in mock_db_conn.execute.mock_calls[1].args[0]
    assert "CREATE OR REPLACE JAVA SCALAR SCRIPT IMPORT_METADATA" in mock_db_conn.execute.mock_calls[2].args[0]
    assert "com.exasol.cloudetl.scriptclasses.FilesMetadataReader" in mock_db_conn.execute.mock_calls[2].args[0]
    assert "CREATE OR REPLACE JAVA SET SCRIPT IMPORT_FILES" in mock_db_conn.execute.mock_calls[3].args[0]
    assert "com.exasol.cloudetl.scriptclasses.FilesDataImporter" in mock_db_conn.execute.mock_calls[3].args[0]
