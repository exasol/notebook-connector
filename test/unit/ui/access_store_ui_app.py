"""
UI app for access store for testing only
"""

from exasol.nb_connector.ui import access_store_ui

ui = access_store_ui.get_access_store_ui()

password = ui.children[0].children[2].children[1]
password.value = "password"

open_button = ui.children[1]
open_button.click()

assert access_store_ui.get_sb_store_file() == access_store_ui.DEFAULT_FILE_NAME
