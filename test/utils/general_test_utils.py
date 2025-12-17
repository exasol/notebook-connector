from __future__ import annotations

import contextlib
from collections.abc import (
    Iterator,
)
from pathlib import Path
from tempfile import TemporaryDirectory


@contextlib.contextmanager
def sample_db_file() -> Iterator[Path]:
    with TemporaryDirectory() as d:
        yield Path(d) / "sample_database.db"
