from pathlib import Path

import ipywidgets as widgets
from IPython import get_ipython

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.popup_message_ui import popup_message
from exasol.nb_connector.ui.ui_styles import get_config_styles

# pylint: disable=global-variable-undefined


def get_access_store_ui(root_dir: str = ".") -> widgets.Widget:

    # Try to find the file name in the shared store.
    # Create a global variable only temporarily.
    ipython = get_ipython()

    # Added this if condition just to enable testing
    if ipython and hasattr(ipython, "run_line_magic"):
        ipython.run_line_magic(
            "store", "-r"
        )  # reloads variables in the IPython user namespace persistence mechanism.

    if "sb_store_file" in globals():
        # pylint: disable=undefined-variable
        global sb_store_file
        sb_store_file_ = sb_store_file
        del sb_store_file
    else:
        sb_store_file_ = "ai_lab_secure_configuration_storage.sqlite"

    ui_look = get_config_styles()

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
    file_txt = widgets.Text(
        value=sb_store_file_, style=ui_look.input_style, layout=ui_look.input_layout
    )
    password_txt = widgets.Password(
        style=ui_look.input_style, layout=ui_look.input_layout
    )
    open_btn = widgets.Button(
        description="Open", style=ui_look.button_style, layout=ui_look.button_layout
    )

    def open_or_create_config_store(btn):
        global ai_lab_config, sb_store_file
        sb_store_file = file_txt.value
        try:
            ai_lab_config = Secrets(Path(root_dir) / sb_store_file, password_txt.value)
            ai_lab_config.connection()
        except:
            popup_message(
                "Failed to open the store. Please check that the password is correct"
            )
        else:
            open_btn.icon = "check"
        finally:
            # Save the file in the shared store.
            # Added this if condition just to enable testing
            if ipython and hasattr(ipython, "run_line_magic"):
                ipython.run_line_magic("store", "sb_store_file")
            del sb_store_file

    def on_value_change(change):
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
    ui = widgets.Box(items, layout=ui_look.outer_layout)
    return ui
