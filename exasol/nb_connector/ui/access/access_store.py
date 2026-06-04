import os
from pathlib import Path

import ipywidgets as widgets
from IPython import get_ipython

from exasol.nb_connector.secret_store import (
    InvalidPassword,
    Secrets,
)
from exasol.nb_connector.ui.common.popup_message import display_popup
from exasol.nb_connector.ui.common.ui_styles import config_styles

DEFAULT_FILE_NAME = "ai_lab_secure_configuration_storage.sqlite"


def get_scs_location_file_path() -> Path:
    """
    Returns the path to the file where the path of the SCS sqlite database file is stored
    """
    return Path.home() / ".cache" / "notebook-connector" / "scs_file"


def _get_scs_path_base(root_dir: str | None) -> Path:
    if root_dir is not None:
        return Path(root_dir)

    notebook_dir = os.environ.get("NOTEBOOK_DIR")
    if notebook_dir:
        return Path(notebook_dir)

    return Path.cwd()


def _resolve_scs_file_path(root_dir: str | None, scs_file: str | Path) -> Path:
    path = Path(scs_file)
    if path.is_absolute():
        return path.resolve()
    return (_get_scs_path_base(root_dir) / path).resolve()


def _display_scs_file_path(root_dir: str | None, scs_file: str | Path) -> str:
    base_dir = _get_scs_path_base(root_dir).resolve()
    resolved_path = _resolve_scs_file_path(root_dir, scs_file)
    try:
        return str(resolved_path.relative_to(base_dir))
    except ValueError:
        return str(resolved_path)


def get_sb_store_file():
    try:
        return get_scs_location_file_path().read_text().strip()
    except FileNotFoundError:
        return DEFAULT_FILE_NAME


def set_sb_store_file(value):
    get_scs_location_file_path().parent.mkdir(parents=True, exist_ok=True)
    get_scs_location_file_path().write_text(value)


def get_access_store(root_dir: str | None = None) -> widgets.Widget:
    sb_store_file = get_sb_store_file()
    sb_store_file_ = _resolve_scs_file_path(root_dir, sb_store_file)
    if not Path(sb_store_file).is_absolute():
        set_sb_store_file(str(sb_store_file_))
    ui_look = config_styles()

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
        value=_display_scs_file_path(root_dir, sb_store_file_),
        style=ui_look.input_style,
        layout=ui_look.input_layout,
    )
    password_txt = widgets.Password(
        style=ui_look.input_style, layout=ui_look.input_layout
    )
    open_btn = widgets.Button(
        description="Open", style=ui_look.button_style, layout=ui_look.button_layout
    )

    def open_or_create_config_store(btn):
        sb_store_file = _resolve_scs_file_path(root_dir, file_txt.value)
        file_txt.value = _display_scs_file_path(root_dir, sb_store_file)
        ipython = get_ipython()
        try:
            ai_lab_config = Secrets(sb_store_file, password_txt.value)
            ai_lab_config.connection()
        except InvalidPassword:
            display_popup(
                "Failed to open the store. Please check that the password is correct"
            )
        else:
            open_btn.icon = "check"
            ipython.push({"ai_lab_config": ai_lab_config}, interactive=True)
        finally:
            set_sb_store_file(str(sb_store_file))

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
