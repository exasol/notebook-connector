import re
from test.unit.cli.scs_mock import ScsMock
from typing import Any
from unittest.mock import (
    Mock,
    create_autospec,
)

import exasol.bucketfs as bfs
import pytest

import exasol.nb_connector.cli.processing.bucketfs_access as bfs_access
from exasol.nb_connector.cli.processing.option_set import ScsCliError


@pytest.fixture
def bfs_mock(monkeypatch):
    """
    Mock the result of open_bucketfs_location().
    """
    mock = create_autospec(bfs.path.PathLike)
    monkeypatch.setattr(
        bfs_access,
        "open_bucketfs_location",
        Mock(return_value=mock),
    )
    return mock


def test_iterdir_fails(bfs_mock):
    """
    Verifying access to the BucketFS starts with creating a sample file.
    Selecting a unique filename requires listing the existing files in the
    BucketFS which is the first operation with a risk of failure.
    """
    scs = ScsMock()
    bfs_mock.iterdir.side_effect = SystemError
    with pytest.raises(SystemError):
        bfs_access.verify_bucketfs_access(scs)


def mock_bfs_file(bfs_mock: Mock, method: str, side_effect: Any) -> Mock:
    """
    Simulate the (mocked) BucketFS to contain a file and a particular
    method of the file having the specified side effect, e.g. raise an
    exception or return a specific value, e.g. content for method
    "file.read()".
    """
    bfs_file = Mock()
    getattr(bfs_file, method).side_effect = side_effect
    bfs_mock.__truediv__.return_value = bfs_file
    return bfs_file


@pytest.mark.parametrize(
    "method, side_effect, expected_message",
    [
        ("write", Exception, "(?s)Couldn't access .*file.write"),
        ("read", Exception, "(?s)Couldn't access .*file.read"),
        ("read", [b"different content"], '"different content" instead of ".*"'),
    ],
)
def test_bfs_exception(bfs_mock, method, side_effect, expected_message):
    """
    This test simulates for the method read() or write() of a file in the
    BucketFS to either raise an exception or to return a specific result.

    The test expects an ScsCliError to be raised and the file to be removed
    from the BucketFS, in spite of the exception.
    """
    file_mock = mock_bfs_file(bfs_mock, method, side_effect)
    scs = ScsMock()
    with pytest.raises(ScsCliError, match=expected_message):
        bfs_access.verify_bucketfs_access(scs)
    assert file_mock.rm.called


def test_bfs_success(bfs_mock, monkeypatch, capsys):
    file_mock = mock_bfs_file(bfs_mock, "read", [b"ABC"])
    monkeypatch.setattr(bfs_access, "random_string", Mock(return_value="ABC"))
    scs = ScsMock()
    bfs_access.verify_bucketfs_access(scs)
    assert file_mock.rm.called
    assert re.match(
        "Access to the BucketFS .* was successful.",
        capsys.readouterr().out,
    )
