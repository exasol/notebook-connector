import os
from enum import Enum

import ipywidgets as widgets
from exasol_integration_test_docker_environment.lib.models.api_errors import (
    TaskFailures,
    TaskRuntimeError,
)

from exasol.nb_connector.ai_lab_config import Accelerator
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.itde_manager import (
    ItdeContainerStatus,
    bring_itde_up,
    get_itde_status,
    restart_itde,
    take_itde_down,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.common.popup_message import display_popup
from exasol.nb_connector.ui.common.ui_styles import config_styles
from exasol.nb_connector.ui.common.useful_urls import Urls
from exasol.nb_connector.ui.config.generic import generic_configuration

DEFAULT_SCHEMA = "Default Schema"


class DockerDbDisplayStatus(Enum):
    """User-facing status messages for the Exasol Docker-DB."""

    READY = "Exasol Docker-DB is READY"
    STOPPED = "Exasol Docker-DB is STOPPED"
    DISCONNECTED = "Exasol Docker-DB is NOT CONNECTED"
    MISSING = "Exasol Docker-DB is NOT CREATED"
    INACCESSIBLE = "Exasol Docker-DB is INACCESSIBLE"


def docker_db_configuration(conf: Secrets) -> widgets.Widget:
    """
    Creates a UI form for editing the Exasol Docker-DB configuration.
    """

    inputs = [
        [
            (
                "Memory Size (GiB)",
                widgets.IntText(value=int(conf.get(CKey.mem_size) or 2)),
                CKey.mem_size,
            ),
            (
                "Disk Size (GiB)",
                widgets.IntText(value=int(conf.get(CKey.disk_size) or 2)),
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

    return generic_configuration(conf, inputs, group_names)


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
            # the situation might have changed while the widgets were hanging around.
            itde_status_now = get_itde_status(conf)
            if itde_status_now != ItdeContainerStatus.READY:
                if itde_status_now == ItdeContainerStatus.ABSENT:
                    bring_itde_up(conf)
                else:
                    restart_itde(conf)
            # Indicate the successful completion.
            display_status.value = DockerDbDisplayStatus.READY.value
            btn.icon = "check"
        except Exception as e:
            display_popup(
                _itde_error_message("Failed to start the Exasol Docker-DB", e)
            )

    def restart_docker_db(btn):
        try:
            # Check if the Docker-DB state has changed since initial display of the UI widgets.
            itde_status_now = get_itde_status(conf)
            if itde_status_now != ItdeContainerStatus.ABSENT:
                take_itde_down(conf)
            bring_itde_up(conf)
            # Indicate the successful completion.
            display_status.value = DockerDbDisplayStatus.READY.value
            btn.icon = "check"
        except Exception as e:
            display_popup(
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


def manage_docker_db(conf: Secrets, socket="/var/run/docker.sock") -> widgets.Widget:
    """
    A UI for starting or restarting the Exasol Docker-DB.
    It checks if an instance of the Exasol Docker-DB is already running or if it exists.
    In that case a warning is displayed.
    """

    if conf.get(CKey.use_itde) != "True":
        return None

    ui_look = config_styles()

    # Check if the docker-socket has been mounted
    socket_mounted = os.path.exists(socket)

    header_lbl = widgets.Label(style=ui_look.header_style, layout=ui_look.header_layout)
    group_items = [header_lbl]

    if socket_mounted:
        # Get and display the current status of the Exasol Docker-DB.
        itde_status = get_itde_status(conf)
        if itde_status == ItdeContainerStatus.READY:
            header_lbl.value = DockerDbDisplayStatus.READY.value
        elif itde_status == ItdeContainerStatus.RUNNING:
            header_lbl.value = DockerDbDisplayStatus.DISCONNECTED.value
        elif itde_status == ItdeContainerStatus.STOPPED:
            header_lbl.value = DockerDbDisplayStatus.STOPPED.value
        else:
            header_lbl.value = DockerDbDisplayStatus.MISSING.value

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

        header_lbl.value = DockerDbDisplayStatus.INACCESSIBLE.value
        warning_text = (
            f"The docker socket is not mounted. Please consult the "
            f'<a href="{Urls.user_manual_docker_db.value}" target="_blank">documentation</a> '
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
