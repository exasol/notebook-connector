import pytest
from unittest import mock
import pathlib
import exasol.bucketfs as bfs
from exasol import bfs_utils


@mock.patch("exasol.bucketfs.Bucket")
def test_put_file_basic(bfs_bucket: mock.MagicMock):
    with pytest.raises(ValueError, match="Local file doesn't exist"):
        bfs_utils.put_file(bfs_bucket, pathlib.Path("non/existent.file"))
