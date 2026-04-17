import os


def test_regression(notebook_runner, notebooks_root) -> None:

    current_dir = os.getcwd()
    try:
        os.chdir(notebooks_root)
        notebook_runner("main_config.ipynb")
        os.chdir("./data")
        notebook_runner("data_abalone.ipynb")
        os.chdir("../sklearn")
        notebook_runner("sklearn_fix_version.ipynb")
        notebook_runner("sklearn_predict_udf.ipynb")
        notebook_runner("sklearn_train_abalone.ipynb")
        notebook_runner("sklearn_predict_abalone.ipynb")
    finally:
        os.chdir(current_dir)


def test_classification(notebook_runner, notebooks_root) -> None:

    current_dir = os.getcwd()
    try:
        os.chdir(notebooks_root)
        notebook_runner("main_config.ipynb")
        os.chdir("./data")
        notebook_runner("data_telescope.ipynb")
        os.chdir("../sklearn")
        notebook_runner("sklearn_fix_version.ipynb")
        notebook_runner("sklearn_predict_udf.ipynb")
        notebook_runner("sklearn_train_telescope.ipynb")
        notebook_runner("sklearn_predict_telescope.ipynb")
    finally:
        os.chdir(current_dir)