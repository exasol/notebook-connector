import os
import textwrap


def test_quickstart(notebook_runner, notebooks_root) -> None:

    data_import_hack = (
        "data_selection",
        textwrap.dedent("""
            load_flights_data(ai_lab_config, ['Jan 2024'])
            load_airlines_data(ai_lab_config)
        """),
    )

    current_dir = os.getcwd()
    try:
        os.chdir(notebooks_root)
        notebook_runner("main_config.ipynb")
        os.chdir("./data")
        notebook_runner("data_flights.ipynb", hacks=[data_import_hack])
        os.chdir("../ibis")
        notebook_runner("quickstart.ipynb")
    finally:
        os.chdir(current_dir)
