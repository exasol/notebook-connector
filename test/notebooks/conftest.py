from pathlib import Path

import pytest

# Re-export fixtures so pytest discovers them when running test/notebooks/ directly.
# pytest only auto-discovers fixtures defined in or imported into conftest.py files.
from test.integration.ui.common.utils.notebook_test_utils import (  # noqa: F401
    backend_setup,
    notebook_runner,
    run_notebook,
    set_log_level_for_libraries,
    uploading_hack,
)

set_log_level_for_libraries()


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