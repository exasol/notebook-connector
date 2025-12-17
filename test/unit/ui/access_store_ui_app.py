"""
UI app for access store for testing only
"""

from IPython import get_ipython

from exasol.nb_connector.ui import access_store_ui

ui = access_store_ui.get_access_store_ui()

password = ui.children[0].children[2].children[1]
password.value = "password"

open_button = ui.children[1]
sb_store_file = None
open_button.click()

#def read_from_store():
#    global sb_store_file
#    sb_store_file = None
#    ipython = get_ipython()
#    ipython.run_line_magic("store", "-r")

#read_from_store()
assert "sb_store_file" in globals(), "sb_store_file was not set by test code!"
assert globals()["sb_store_file"] == access_store_ui.DEFAULT_FILE_NAME
