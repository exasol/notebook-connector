import os
from enum import Enum

import ipywidgets as widgets
from exasol_integration_test_docker_environment.lib.models.api_errors import (
    TaskFailures,
    TaskRuntimeError,
)

from exasol.nb_connector.ai_lab_config import Accelerator
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.connections import get_backend
from exasol.nb_connector.itde_manager import (
    ItdeContainerStatus,
    bring_itde_up,
    get_itde_status,
    restart_itde,
    take_itde_down,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.generic_config_ui import get_generic_config_ui
from exasol.nb_connector.ui.popup_message_ui import popup_message
from exasol.nb_connector.ui.ui_styles import get_config_styles

DEFAULT_SCHEMA = "Default Schema"


class ITDEStatus(Enum):
    """
    Display status of the Exasol Docker-DB
    """

    ready = "Exasol Docker-DB is READY"
    stopped = "Exasol Docker-DB is STOPPED"
    disconnected = "Exasol Docker-DB is NOT CONNECTED"
    missing = "Exasol Docker-DB is NOT CREATED"
    inaccessible = "Exasol Docker-DB is INACCESSIBLE"


def get_db_selection_ui(conf: Secrets) -> widgets.Widget:
    """
    Creates a UI form for choosing between the Exasol Docker-DB and an external Exasol Database.
    """

    ui_look = get_config_styles()

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
        select_btn.icon = "pen"

    select_btn.on_click(select_database)
    db_selector.observe(on_value_change, names=["value"])

    group_items = [header_lbl, widgets.Box([db_selector], layout=ui_look.row_layout)]
    items = [widgets.Box(group_items, layout=ui_look.group_layout), select_btn]
    ui = widgets.Box(items, layout=ui_look.outer_layout)
    return ui


def get_onprem_db_config_ui(conf: Secrets) -> widgets.Widget:
    """
    Creates a UI form for editing an external Exasol Database configuration.
    """

    inputs = [
        [
            (
                "Host Name",
                widgets.Text(value=conf.get(CKey.db_host_name, "localhost")),
                CKey.db_host_name,
            ),
            (
                "Port",
                widgets.IntText(value=int(conf.get(CKey.db_port, "8563"))),
                CKey.db_port,
            ),
            ("User Name", widgets.Text(value=conf.get(CKey.db_user)), CKey.db_user),
            (
                "Password",
                widgets.Password(value=conf.get(CKey.db_password)),
                CKey.db_password,
            ),
            (
                DEFAULT_SCHEMA,
                widgets.Text(value=conf.get(CKey.db_schema, "AI_LAB")),
                CKey.db_schema,
            ),
            (
                "Encrypted Comm.",
                widgets.Checkbox(
                    value=conf.get(CKey.db_encryption, "True") == "True", indent=False
                ),
                CKey.db_encryption,
            ),
        ],
        [
            (
                "External Host Name",
                widgets.Text(value=conf.get(CKey.bfs_host_name, "localhost")),
                CKey.bfs_host_name,
            ),
            (
                "Internal Host Name",
                widgets.Text(value=conf.get(CKey.bfs_host_name, "localhost")),
                CKey.bfs_internal_host_name,
            ),
            (
                "External Port",
                widgets.IntText(value=int(conf.get(CKey.bfs_port, "2580"))),
                CKey.bfs_port,
            ),
            (
                "Internal Port",
                widgets.IntText(value=int(conf.get(CKey.bfs_port, "2580"))),
                CKey.bfs_internal_port,
            ),
            ("User Name", widgets.Text(value=conf.get(CKey.bfs_user)), CKey.bfs_user),
            (
                "Password",
                widgets.Password(value=conf.get(CKey.bfs_password)),
                CKey.bfs_password,
            ),
            (
                "Service Name",
                widgets.Text(value=conf.get(CKey.bfs_service, "bfsdefault")),
                CKey.bfs_service,
            ),
            (
                "Bucket Name",
                widgets.Text(value=conf.get(CKey.bfs_bucket, "default")),
                CKey.bfs_bucket,
            ),
            (
                "Encrypted Comm.",
                widgets.Checkbox(
                    value=conf.get(CKey.bfs_encryption, "True") == "True", indent=False
                ),
                CKey.bfs_encryption,
            ),
        ],
        [
            (
                "Validate Certificate",
                widgets.Checkbox(
                    value=conf.get(CKey.cert_vld, "True") == "True", indent=False
                ),
                CKey.cert_vld,
            ),
            (
                "Trusted CA File/Dir",
                widgets.Text(value=conf.get(CKey.trusted_ca)),
                CKey.trusted_ca,
            ),
            (
                "Certificate File",
                widgets.Text(value=conf.get(CKey.client_cert)),
                CKey.client_cert,
            ),
            (
                "Private Key File",
                widgets.Text(value=conf.get(CKey.client_key)),
                CKey.client_key,
            ),
        ],
    ]

    group_names = [
        "Database Connection",
        "BucketFS Connection",
        "TLS/SSL Configuration",
    ]

    return get_generic_config_ui(conf, inputs, group_names)


def get_saas_db_config_ui(conf: Secrets) -> widgets.Widget:
    """
    Creates a UI form for editing the Exasol SaaS database configuration.
    """

    inputs = [
        [
            (
                "Service URL",
                widgets.Text(value=conf.get(CKey.saas_url, "https://cloud.exasol.com")),
                CKey.saas_url,
            ),
            (
                "Account ID",
                widgets.Password(value=conf.get(CKey.saas_account_id)),
                CKey.saas_account_id,
            ),
            (
                "Database ID",
                widgets.Text(value=conf.get(CKey.saas_database_id)),
                CKey.saas_database_id,
            ),
            (
                "Database Name",
                widgets.Text(value=conf.get(CKey.saas_database_name)),
                CKey.saas_database_name,
            ),
            (
                "Personal Access Token",
                widgets.Password(value=conf.get(CKey.saas_token)),
                CKey.saas_token,
            ),
            (
                DEFAULT_SCHEMA,
                widgets.Text(value=conf.get(CKey.db_schema, "AI_LAB")),
                CKey.db_schema,
            ),
        ],
        [
            (
                "Validate Certificate",
                widgets.Checkbox(
                    value=conf.get(CKey.cert_vld, "True") == "True", indent=False
                ),
                CKey.cert_vld,
            ),
            (
                "Trusted CA File/Dir",
                widgets.Text(value=conf.get(CKey.trusted_ca)),
                CKey.trusted_ca,
            ),
        ],
    ]

    group_names = ["SaaS DB Configuration", "TLS/SSL Configuration"]

    return get_generic_config_ui(conf, inputs, group_names)


def get_docker_db_config_ui(conf: Secrets) -> widgets.Widget:
    """
    Creates a UI form for editing the Exasol Docker-DB configuration.
    """

    inputs = [
        [
            (
                "Memory Size (GiB)",
                widgets.IntText(value=int(conf.get(CKey.mem_size, "2"))),
                CKey.mem_size,
            ),
            (
                "Disk Size (GiB)",
                widgets.IntText(value=int(conf.get(CKey.disk_size, "2"))),
                CKey.disk_size,
            ),
            (
                "Accelerator",
                widgets.Dropdown(
                    value=conf.get(CKey.accelerator, "none"),
                    options=[x.value for x in Accelerator],
                ),
                CKey.accelerator,
            ),
            (
                DEFAULT_SCHEMA,
                widgets.Text(value=conf.get(CKey.db_schema, "AI_LAB")),
                CKey.db_schema,
            ),
        ]
    ]

    group_names = ["Database Configuration"]

    return get_generic_config_ui(conf, inputs, group_names)


def get_db_config_ui(conf: Secrets) -> widgets.Widget:
    """
    Creates a db configuration UI, depending on the choice of the database.
    """
    storage_backend = get_backend(conf)
    if storage_backend == StorageBackend.saas:
        return get_saas_db_config_ui(conf)
    elif conf.get(CKey.use_itde, "True") == "True":
        return get_docker_db_config_ui(conf)
    else:
        return get_onprem_db_config_ui(conf)


def _itde_error_message(header: str, e: Exception) -> str:
    if isinstance(e, TaskRuntimeError):
        if isinstance(e.__cause__, TaskFailures):
            err_message = f"{e.msg} {e.__cause__}"
        elif e.inner:
            causes = "\n".join(e.inner)
            err_message = f"{e.msg} This was caused by\n{causes}"
        else:
            err_message = e.msg
    else:
        err_message = str(e)
    return f"{header}: {err_message}"


def _get_docker_db_action_buttons(
        conf: Secrets, itde_exists: bool, itde_ready: bool, display_status: widgets.Widget
) -> list[widgets.Button]:
    """
    Creates one or two action buttons with the correspondent on_click functions for managing the
    Exasol Docker-DB. Depending on the current status (idte_exists, itde_ready) of the docker
    container, the "Start", "Restart" or both buttons are created.
    When the action is completed successfully, the running status is displayed in the provided
    widget (display_status).
    """

    def start_docker_db(btn):
        try:
            # Need to check if the Exasol Docker-DB still exists and not running because
            # the situation might have changed while the the widgets were hanging around.
            itde_status_now = get_itde_status(conf)
            if itde_status_now != ItdeContainerStatus.READY:
                if itde_status_now == ItdeContainerStatus.ABSENT:
                    bring_itde_up(conf)
                else:
                    restart_itde(conf)
            # Indicate the successful completion.
            display_status.value = ITDEStatus.ready.value
            btn.icon = "check"
        except Exception as e:
            popup_message(
                _itde_error_message("Failed to start the Exasol Docker-DB", e)
            )

    def restart_docker_db(btn):
        try:
            # Need to check again if the Exasol Docker-DB exists or not because
            # the situation might have changed while the widgets were hanging around.
            itde_status_now = get_itde_status(conf)
            if itde_status_now != ItdeContainerStatus.ABSENT:
                take_itde_down(conf)
            bring_itde_up(conf)
            # Indicate the successful completion.
            display_status.value = ITDEStatus.ready.value
            btn.icon = "check"
        except Exception as e:
            popup_message(
                _itde_error_message("Failed to restart the Exasol Docker-DB:", e)
            )

    if itde_ready:
        btn_restart = widgets.Button(description="Recreate and Start")
        btn_restart.on_click(restart_docker_db)
        return [btn_restart]
    elif itde_exists:
        btn_start = widgets.Button(description="Start")
        btn_start.on_click(start_docker_db)
        btn_restart = widgets.Button(description="Recreate and Start")
        btn_restart.on_click(restart_docker_db)
        return [btn_start, btn_restart]
    else:
        btn_start = widgets.Button(description="Create and Start")
        btn_start.on_click(start_docker_db)
        return [btn_start]


def _create_warning(warning_text: str) -> widgets.Widget:
    return widgets.HTML(
        value="<style>p.itde_warning{word-wrap: break-word; color: red;}</style>"
              '<p class="itde_warning">' + warning_text + " </p>"
    )


def get_start_docker_db_ui(conf: Secrets) -> widgets.Widget:
    """
    A UI for starting or restarting the Exasol Docker-DB.
    It checks if an instance of the Exasol Docker-DB is already running or if it exists.
    In that case a warning is displayed.
    """

    if conf.get(CKey.use_itde) != "True":
        return None

    ui_look = get_config_styles()

    # Check if the docker-socket has been mounted
    socket_mounted = os.path.exists("/var/run/docker.sock")

    header_lbl = widgets.Label(style=ui_look.header_style, layout=ui_look.header_layout)
    group_items = [header_lbl]

    if socket_mounted:
        # Get and display the current status of the Exasol Docker-DB.
        itde_status = get_itde_status(conf)
        if itde_status == ItdeContainerStatus.READY:
            header_lbl.value = ITDEStatus.ready.value
        elif itde_status == ItdeContainerStatus.RUNNING:
            header_lbl.value = ITDEStatus.disconnected.value
        elif itde_status == ItdeContainerStatus.STOPPED:
            header_lbl.value = ITDEStatus.stopped.value
        else:
            header_lbl.value = ITDEStatus.missing.value

        # Add a warning message about recreating an existing Exasol Docker-DB.
        itde_exists = itde_status != ItdeContainerStatus.ABSENT
        itde_ready = itde_status == ItdeContainerStatus.READY
        if itde_exists:
            warning_text = (
                "Please note that recreating the Exasol Docker-DB will result in the loss of all data stored in the "
                f'{"running" if itde_ready else "existing"} instance of the database!'
            )
            warning_html = _create_warning(warning_text)
            group_items.append(widgets.Box([warning_html], layout=ui_look.row_layout))

        # Create action buttons.
        action_buttons = _get_docker_db_action_buttons(
            conf, itde_exists, itde_ready, header_lbl
        )
        for btn in action_buttons:
            btn.style = ui_look.button_style
            btn.layout = ui_look.button_layout
    else:
        from useful_urls import UsefulURLs

        header_lbl.value = ITDEStatus.inaccessible.value
        warning_text = (
            f"The docker socket is not mounted. Please consult the "
            f'<a href="{UsefulURLs.user_manual_docker_db.value}" target="_blank">documentation</a> '
            "on how to start the AI-Lab that will use the Integrated Exasol Docker-DB."
        )
        warning_html = _create_warning(warning_text)
        group_items.append(widgets.Box([warning_html], layout=ui_look.row_layout))
        action_buttons = []

    # Put all UI elements together.
    items = [
        widgets.Box(group_items, layout=ui_look.group_layout),
        widgets.Box(action_buttons, layout=ui_look.row_layout),
    ]
    ui = widgets.Box(items, layout=ui_look.outer_layout)
    return ui
