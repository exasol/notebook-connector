import pytest
from unittest import mock
from typing import Generator
import pathlib
from exasol import bfs_utils


MOCKED_BUCKET = "bucket"
MOCKED_FILE_NAME = "bfs.file"


@mock.patch("exasol.bucketfs.Bucket")
def test_put_file_basic(bfs_bucket: mock.MagicMock):
    with pytest.raises(ValueError, match="Local file doesn't exist"):
        bfs_utils.put_file(bfs_bucket, pathlib.Path("non/existent/local.file"))


@pytest.fixture
@mock.patch("exasol.bucketfs.Bucket")
def bucket_with_file(bfs_bucket: mock.MagicMock):
    bfs_bucket.name = MOCKED_BUCKET
    bfs_bucket.__iter__.return_value = iter([MOCKED_FILE_NAME])
    bfs_bucket.upload.return_value = None
    return bfs_bucket


@pytest.fixture
def temp_file(tmp_path) -> Generator[pathlib.Path, None, None]:
    path = pathlib.Path(tmp_path) / MOCKED_FILE_NAME
    path.write_text("data")
    yield path
    path.unlink()


def test_put_file_exists(caplog, bucket_with_file, temp_file):
    caplog.set_level("INFO")
    path = bfs_utils.put_file(bucket_with_file, temp_file)
    assert str(path) == f"/buckets/bfsdefault/{MOCKED_BUCKET}/{MOCKED_FILE_NAME}"
    assert "already present in the bucketfs" in caplog.text
    assert not bucket_with_file.upload.called

    caplog.clear()
    path = bfs_utils.put_file(bucket_with_file, temp_file, skip_if_exists=False)
    assert str(path) == f"/buckets/bfsdefault/{MOCKED_BUCKET}/{MOCKED_FILE_NAME}"
    assert bucket_with_file.upload.called
    assert "Uploading file" in caplog.text
