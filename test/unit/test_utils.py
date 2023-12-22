import os
from tempfile import TemporaryDirectory

import pytest

from exasol.utils import upward_file_search


def test_upward_file_search():
    current_dir = os.getcwd()
    try:
        dir_to_search = "the dir"
        file_to_search = "the file"
        path_to_search = '/'.join([dir_to_search, file_to_search])
        with TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            os.mkdir(dir_to_search)
            open(path_to_search, "w").close()
            sub_dir = os.path.join(tmp_dir, "new_current")
            os.mkdir(sub_dir)
            os.chdir(sub_dir)
            file_path = upward_file_search(path_to_search)
            assert file_path == os.path.join(tmp_dir, path_to_search)
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
