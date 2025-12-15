"""
UI app for access store for testing only
"""

import sys

import ipywidgets
from IPython import get_ipython

from exasol.nb_connector.ui import access_store_ui

DEFAULT_FILE_NAME = "ai_lab_secure_configuration_storage.sqlite"

ui = access_store_ui.get_access_store_ui()

test_text = ipywidgets.Text(value="init")
test_btn = ipywidgets.Button(description="Test")


def read_store_magic(btn):
    """
    Called when a test_button is clicked to fetch the sb_store_file from store magic
    """
    ipython = get_ipython()
    user_ns = ipython.user_ns
    try:
        ipython.run_line_magic("store", "-r")
        value = globals().get("sb_store_file")
        if value is not None:
            test_text.value = value
            print("sb_store_file:", value)
        else:
            test_text.value = "sb_store_file not set"
            print("sb_store_file not set!")
    except Exception as e:
        print("Error in read_store_magic:", e, file=sys.stderr)


test_btn.on_click(read_store_magic)

items = [ui, test_text, test_btn]
app = ipywidgets.Box(items)

password = app.children[0].children[0].children[2].children[1]
password.value = "password"

open_button = app.children[0].children[1]
open_button.click()

test_button = app.children[2]
# test_button.click()
IPYTHON = get_ipython()
assert (
    "sb_store_file" in globals()
), "sb_store_file was not set by test code!"
assert globals()["sb_store_file"] == DEFAULT_FILE_NAME
