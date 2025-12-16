"""
UI app for access store for testing only
"""

from IPython import get_ipython

from exasol.nb_connector.ui import access_store_ui

sb_store_file = "ai_lab_secure_configuration_storage.sqlite"

ui = access_store_ui.get_access_store_ui()

password = ui.children[0].children[2].children[1]
password.value = "password"

open_button = ui.children[1]
open_button.click()

ipython = get_ipython()
ipython.run_line_magic("store", "-r")
assert "sb_store_file" in globals(), "sb_store_file was not set by test code!"
assert globals()["sb_store_file"] == sb_store_file
