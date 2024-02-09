import os
from tempfile import TemporaryDirectory

import pytest

from exasol.nb_connector.utils import upward_file_search, optional_str_to_bool


def test_upward_file_search():
    current_dir = os.getcwd()
    try:
        file_to_search = "the file"
        with TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            open(file_to_search, "w").close()
            sub_dir = os.path.join(tmp_dir, "new_current")
            os.mkdir(sub_dir)
            os.chdir(sub_dir)
            file_path = upward_file_search(file_to_search)
            assert file_path == os.path.join(tmp_dir, file_path)
    finally:
        os.chdir(current_dir)


def test_upward_file_search_failure():
    current_dir = os.getcwd()
    try:
        file_to_search = "# impossible file #"
        with TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            with pytest.raises(ValueError):
                upward_file_search(file_to_search)
    finally:
        os.chdir(current_dir)


@pytest.mark.parametrize("v, expected", [
    (None, None),
    ('y', True),
    ('yes', True),
    ('true', True),
    ('Y', True),
    ('YES', True),
    ('TRUE', True),
    ('n', False),
    ('no', False),
    ('false', False),
    ('N', False),
    ('NO', False),
    ('FALSE', False)
])
def test_optional_str_to_bool(v, expected):
    assert optional_str_to_bool(v) == expected
