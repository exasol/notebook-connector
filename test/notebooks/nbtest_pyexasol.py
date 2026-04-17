import os


def test_roundtrip_import_and_export(notebook_runner, notebooks_root) -> None:
    current_dir = os.getcwd()
    try:
        os.chdir(notebooks_root)
        notebook_runner("main_config.ipynb")
        os.chdir("./pyexasol")
        notebook_runner("roundtrip_import_and_export.ipynb")
    finally:
        os.chdir(current_dir)