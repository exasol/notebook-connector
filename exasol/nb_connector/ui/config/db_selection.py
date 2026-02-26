import ipywidgets as widgets

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.connections import get_backend
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.common.ui_styles import config_styles


def get_selection(conf: Secrets) -> widgets.Widget:
    """
    Creates a UI form for choosing between the Exasol Docker-DB and an external Exasol Database.
    """

    ui_look = config_styles()

    db_options = ["Exasol Docker-DB", "Exasol On-Prem Database", "Exasol SaaS Database"]
    storage_backend = get_backend(conf)
    if storage_backend == StorageBackend.saas:
        db_choice = 2
    elif conf.get(CKey.use_itde, "True") == "True":
        db_choice = 0
    else:
        db_choice = 1
    db_selector = widgets.RadioButtons(
        options=db_options,
        value=db_options[db_choice],
        layout=ui_look.input_layout,
        style=ui_look.input_style,
    )
    select_btn = widgets.Button(
        description="Select", style=ui_look.button_style, layout=ui_look.button_layout
    )
    header_lbl = widgets.Label(
        value="Exasol Database Choice",
        style=ui_look.header_style,
        layout=ui_look.header_layout,
    )

    def select_database(btn):
        if db_selector.value == db_options[2]:
            conf.save(CKey.storage_backend, StorageBackend.saas.name)
        else:
            conf.save(CKey.storage_backend, StorageBackend.onprem.name)
            conf.save(CKey.use_itde, str(db_selector.value == db_options[0]))
        btn.icon = "check"

    def on_value_change(change):
        select_btn.icon = "pencil"

    select_btn.on_click(select_database)
    db_selector.observe(on_value_change, names=["value"])

    group_items = [header_lbl, widgets.Box([db_selector], layout=ui_look.row_layout)]
    items = [widgets.Box(group_items, layout=ui_look.group_layout), select_btn]
    ui = widgets.Box(items, layout=ui_look.outer_layout)
    return ui
