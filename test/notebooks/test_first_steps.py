import os


def test_first_steps_notebook(notebook_runner, notebooks_root) -> None:
    os.chdir(notebooks_root)
    notebook_runner("main_config.ipynb")
    notebook_runner("first_steps.ipynb")
