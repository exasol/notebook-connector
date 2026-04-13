from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def notebooks_root() -> Path:
    notebooks_dir = (
        Path(__file__).resolve().parents[2]
        / "exasol"
        / "nb_connector"
        / "resources"
        / "notebooks"
    )
    if not notebooks_dir.is_dir():
        raise FileNotFoundError(f"Notebook directory not found: {notebooks_dir}")
    return notebooks_dir
