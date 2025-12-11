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
    import sys
    from IPython import get_ipython
    ipython = get_ipython()
    user_ns = ipython.user_ns
    try:
        print("read_store_magic function try block")
        if ipython and hasattr(ipython, "run_line_magic"):
            ipython.run_cell_magic("store", "-r", "")
        value = user_ns.get("sb_store_file", None)  # Safely get the value
        if value is not None:
            test_text.value = value
            print("sb_store_file:", value)
        else:
            test_text.value = "sb_store_file not set"
            print("sb_store_file not set!")
    except Exception as e:
        print("Error in read_store_magic:", e, file=sys.stderr)
        with open("test_file.txt", "w") as f:
            f.write(f"{e}")

test_btn.on_click(read_store_magic)

items = [ui, test_text, test_btn]
app = ipywidgets.Box(items)
