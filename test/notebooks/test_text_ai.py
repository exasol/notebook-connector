import os


def test_text_ai(
    notebook_runner, backend_setup, uploading_hack, notebooks_root
) -> None:
    """
    This test currently requires some specific Jupyter notebooks which are work in progress
    and is only executed if the folder work_in_progress exists.
    """
    store_path, store_password = backend_setup

    current_dir = os.getcwd()
    try:
        os.chdir(notebooks_root)
        notebook_runner("main_config.ipynb")
        os.chdir("data")
        notebook_runner(
            notebook_file="data_customer_support.ipynb", hacks=[uploading_hack]
        )
        os.chdir(notebooks_root)
        os.chdir("text_ai")
        result = notebook_runner(
            notebook_file="txaie_init.ipynb", hacks=[uploading_hack]
        )
        notebook_runner(
            notebook_file="txaie_preprocessing.ipynb", hacks=[uploading_hack]
        )
    finally:
        os.chdir(current_dir)
