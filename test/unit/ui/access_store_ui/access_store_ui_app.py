"""
UI app for the Access Store
"""

from pathlib import Path

import ipywidgets as widgets
from IPython import get_ipython

from exasol.nb_connector.secret_store import (
    InvalidPassword,
    Secrets,
)
from exasol.nb_connector.ui.popup_message_ui import popup_message
from exasol.nb_connector.ui.ui_styles import get_config_styles

# pylint-disable and type-ignore are added in this file because this code
# is intended to be run in jupyter notebook

# pylint: disable=global-variable-undefined

DEFAULT_FILE_NAME = "ai_lab_secure_configuration_storage.sqlite"

ui_look = get_config_styles()

# File path input
file_txt = widgets.Text(
    value=DEFAULT_FILE_NAME, style=ui_look.input_style, layout=ui_look.input_layout
)

# Password input
password_txt = widgets.Password(style=ui_look.input_style, layout=ui_look.input_layout)

# UI Elements
header_lbl = widgets.Label(
    value="Configuration Store",
    style=ui_look.header_style,
    layout=ui_look.header_layout,
)
file_lbl = widgets.Label(
    value="File Path", style=ui_look.label_style, layout=ui_look.label_layout
)
password_lbl = widgets.Label(
    value="Password", style=ui_look.label_style, layout=ui_look.label_layout
)
open_btn = widgets.Button(
    description="Open", style=ui_look.button_style, layout=ui_look.button_layout
)


def open_or_create_config_store():
    global ai_lab_config
    sb_store_file = file_txt.value
    ipython = get_ipython()
    try:
        ai_lab_config = Secrets(Path(sb_store_file), password_txt.value)
        ai_lab_config.connection()
    except InvalidPassword:
        popup_message(
            "Failed to open the store. Please check that the password is correct"
        )
    else:
        open_btn.icon = "check"
    finally:
        # Save the file path variable to the shared store (IPython only)
        if ipython and hasattr(ipython, "run_line_magic"):
            ipython.run_line_magic("store", "sb_store_file")
        del sb_store_file


def on_value_change():
    open_btn.icon = "pen"


open_btn.on_click(open_or_create_config_store)
file_txt.observe(on_value_change, names=["value"])
password_txt.observe(on_value_change, names=["value"])


group_items = [
    header_lbl,
    widgets.Box([file_lbl, file_txt], layout=ui_look.row_layout),
    widgets.Box([password_lbl, password_txt], layout=ui_look.row_layout),
]
items = [widgets.Box(group_items, layout=ui_look.group_layout), open_btn]
app = widgets.Box(items, layout=ui_look.outer_layout)
