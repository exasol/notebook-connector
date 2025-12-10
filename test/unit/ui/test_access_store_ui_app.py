import importlib.resources
import logging

from solara.server import reload

logger = logging.getLogger("solara.server.access_store_app_test")

ACCESS_STORE_APP_SRC = (
    importlib.resources.files("test.unit.ui") / "access_store_ui_app.py"
)
reload.reloader.start()

NEW_FILE_NAME = "new_file.sqlite"
TEST_PASSWORD = "password"


def test_new_read_test():
    import IPython.core.interactiveshell

    shell = IPython.core.interactiveshell.InteractiveShell.instance()
    script_path = "test/unit/ui/access_store_ui_app.py"

    print("--- Running IPython script ---")
    shell.run_line_magic("run", script_path)

    print("--- Back in Python script ---")
    app = shell.user_ns["app"]

    password = app.children[0].children[0].children[2].children[1]
    password.value = "password"

    open_button = app.children[0].children[1]
    open_button.click()

    test_button = app.children[2]
    test_button.click()

    assert shell.user_ns["sb_store_file"] == ""



def test_run_cell_test():
    from IPython.terminal.embed import run_cell
    ipython_code = """
# here needs to go the content of access_store_ui_app.py

    password = app.children[0].children[0].children[2].children[1]
    password.value = "password"

    open_button = app.children[0].children[1]
    open_button.click()

    test_button = app.children[2]
    test_button.click()

    assert shell.user_ns["sb_store_file"] == ""
    """

    # Execute the cell
    result = run_cell(ipython_code)