import os
import shutil
from pathlib import Path
from test.integration.ui.common.utils.notebook_test_utils import run_notebook

import pytest
from exasol.pytest_backend import BACKEND_ONPREM


@pytest.fixture()
def cleanup_slc_repo_dir(backend, notebooks_root):
    yield
    if backend == BACKEND_ONPREM:
        p = notebooks_root / "script_languages_container" / "slc_workspace"
        shutil.rmtree(p)


def test_script_languages_container(
    backend, backend_setup, cleanup_slc_repo_dir, notebooks_root
) -> None:
    if backend != BACKEND_ONPREM:
        pytest.skip()
    current_dir = Path.cwd()
    store_path, store_password = backend_setup
    store_file = str(store_path)
    try:
        os.chdir(notebooks_root)
        run_notebook("main_config.ipynb", store_file, store_password)
        os.chdir("./script_languages_container")
        run_notebook("configure_slc_repository.ipynb", store_file, store_password)
        run_notebook("export_as_is.ipynb", store_file, store_password)
        run_notebook("customize.ipynb", store_file, store_password)
        run_notebook("test_slc.ipynb", store_file, store_password)
        run_notebook("advanced.ipynb", store_file, store_password)
        run_notebook(
            "using_the_script_languages_container_tool.ipynb",
            store_file,
            store_password,
        )
    finally:
        os.chdir(current_dir)
