import os


def test_cloud_notebook(notebook_runner, notebooks_root) -> None:
    current_dir = os.getcwd()
    try:
        os.chdir(notebooks_root)
        notebook_runner("main_config.ipynb")
        os.chdir("cloud")
        notebook_runner("01_import_data.ipynb")
    finally:
        os.chdir(current_dir)


def test_s3_vs_notebook(notebook_runner, notebooks_root) -> None:
    current_dir = os.getcwd()
    try:
        os.chdir(notebooks_root)
        notebook_runner("main_config.ipynb")
        os.chdir("cloud")
        notebook_runner("02_s3_vs_reuters.ipynb")
    finally:
        os.chdir(current_dir)