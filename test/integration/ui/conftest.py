from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope="session")
def solara_snapshots_directory(request: Any) -> Path:
    path = Path(request.config.rootpath) / "ui_snapshots"
    if not path.exists():
        path.mkdir(exist_ok=True, parents=True)
    return path
