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
        # del ipython.user_ns['sb_store_file']
        #
        ipython.run_line_magic("store", "-r")

        test_text.value = ipython.user_ns["sb_store_file"]
    except Exception as e:
        with open("test_file.txt", "w") as f:
            f.write(f"{e}")


test_btn.on_click(read_store_magic)

items = [ui, test_text, test_btn]
app = ipywidgets.Box(items)
