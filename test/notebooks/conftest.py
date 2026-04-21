from pathlib import Path

import pytest

from test.integration.ui.common.utils.notebook_test_utils import set_log_level_for_libraries

set_log_level_for_libraries()


@pytest.fixture(scope="session")
def notebooks_root() -> Path:
    """
    Returns the root of the notebooks directory
    """
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