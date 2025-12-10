import importlib.resources
import logging

from solara.server import reload
from tqdm.autonotebook import get_ipython

logger = logging.getLogger("solara.server.access_store_app_test")

ACCESS_STORE_APP_SRC = (
        importlib.resources.files("test.unit.ui") / "access_store_ui_app.py"
)
reload.reloader.start()

NEW_FILE_NAME = "new_file.sqlite"
TEST_PASSWORD = "password"


def test_shell():
    import IPython.core.interactiveshell

    shell = IPython.core.interactiveshell.InteractiveShell.instance()
    ipython_code = """
    print("testing shell print")
    """
    result = shell.run_cell(ipython_code)


def test_dummy():
    from IPython.testing.globalipapp import get_ipython
    ipython = get_ipython()
    ipython.run_cell("testing IPython.testing.globalipapp.get_ipython")

def test_shell_store():
    import IPython.core.interactiveshell
    shell = IPython.core.interactiveshell.InteractiveShell.instance()
    shell.run_line_magic("run", "test/unit/ui/access_store_ui_app.py")
    assert "sb_store_file" in shell.user_ns.keys()


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
    handler = test_button._click_handlers.callbacks[0]
    handler(test_button)
    # test_button.click()
    print(shell.user_ns.keys())
    assert "sb_store_file" in shell.user_ns, "sb_store_file was not set by test code!"
    assert shell.user_ns["sb_store_file"] == ""


def test_run_cell_test():
    # from IPython.terminal.embed import run_cell
    import IPython.core.interactiveshell

    shell = IPython.core.interactiveshell.InteractiveShell.instance()
    ipython_code = """
    # here needs to go the content of access_store_ui_app.py
    
    import IPython.core.interactiveshell

    shell = IPython.core.interactiveshell.InteractiveShell.instance()
    import ipywidgets
    from IPython import get_ipython
    
    from exasol.nb_connector.ui import access_store_ui
    
    # from IPython.testing.globalipapp import get_ipython
    
    DEFAULT_FILE_NAME = "ai_lab_secure_configuration_storage.sqlite"
    # import and get ui
    ui = access_store_ui.get_access_store_ui()
    
    
    test_text = ipywidgets.Text(value="init")
    test_btn = ipywidgets.Button(description="Test")
    
    
    def read_store_magic(btn):
        # raise Exception("Experiment")
        try:
            ipython = get_ipython()
            ipython.run_line_magic("store", "-r")
        
            test_text.value = ipython.user_ns["sb_store_file"]
            print(test_text.value)
            print(ipython.user_ns["sb_store_file"])
        except Exception as e:
            with open("test_file.txt", "w") as f:
                f.write(f"{e}")
    
    
    test_btn.on_click(read_store_magic)
    
    items = [ui, test_text, test_btn]
    app = ipywidgets.Box(items)

    password = app.children[0].children[0].children[2].children[1]
    password.value = "password"

    open_button = app.children[0].children[1]
    open_button.click()

    test_button = app.children[2]
    test_button.click()
    print(shell.user_ns.keys())
    assert shell.user_ns["sb_store_file"] == ""
    """

    # Execute the cell
    result = shell.run_cell(ipython_code)

