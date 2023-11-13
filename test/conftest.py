from pathlib import Path

import pytest

from exasol.secret_store import Secrets


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    return tmp_path / "sample_database.db"


@pytest.fixture
def secrets(sample_file) -> Path:  # pylint: disable=W0621
    return Secrets(sample_file, master_password="abc")
