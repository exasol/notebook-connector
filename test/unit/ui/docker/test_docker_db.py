import os

import ipywidgets as widgets
from exasol_integration_test_docker_environment.lib.models.api_errors import (
    TaskRuntimeError,
)

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.docker import docker_db


def create_secrets(tmp_path: os.PathLike) -> Secrets:
    """Create a secrets store for tests."""
    return Secrets(tmp_path / "secrets.db", "test-password")


def header_label_from_ui(ui):
    """Return the header label widget from the UI."""
    group_box = ui.children[0]
    return group_box.children[0]


def _mem_disk_widgets(ui):
    """Return the memory and disk widgets from the UI."""
    group_box = ui.children[0]
    mem_row = group_box.children[1]
    disk_row = group_box.children[2]
    return mem_row.children[1], disk_row.children[1]


def test_docker_db_configuration_defaults(tmp_path):
    """Check default memory and disk widget values."""
    conf = create_secrets(tmp_path)

    ui = docker_db.docker_db_configuration(conf)
    mem_widget, disk_widget = _mem_disk_widgets(ui)

    assert isinstance(mem_widget, widgets.IntText)
    assert isinstance(disk_widget, widgets.IntText)
    assert mem_widget.value == 2
    assert disk_widget.value == 2


def test_itde_error_message_non_task_runtime_error():
    """Format error message for a non-task runtime error."""
    err = ValueError("boom")
    msg = docker_db._itde_error_message("Header", err)
    assert msg == "Header: boom"


def test_itde_error_message_task_runtime_error_inner():
    """Format error message for a task runtime error with inner list."""
    err = TaskRuntimeError("oops", inner=["a", "b"])
    msg = docker_db._itde_error_message("Header", err)
    assert msg == "Header: oops This was caused by\na\nb"


def test_create_warning_widget_contains_text():
    """Create a warning widget with the given text."""
    warning = docker_db._create_warning("hello")
    assert isinstance(warning, widgets.HTML)
    assert "hello" in warning.value


def test_docker_action_configuration_use_itde_false(tmp_path):
    """Return None when ITDE use is disabled."""
    conf = create_secrets(tmp_path)
    conf.save(CKey.use_itde, "False")
    assert docker_db.manage_docker_db(conf) is None


def test_docker_action_configuration_no_itde_container(tmp_path, monkeypatch):
    """Show missing container state when socket exists but no container."""
    conf = create_secrets(tmp_path)
    conf.save(CKey.use_itde, "True")

    socket_path = tmp_path / "docker.sock"
    socket_path.touch()
    monkeypatch.setattr(os.path, "exists", lambda p: str(p) == str(socket_path))

    ui = docker_db.manage_docker_db(conf, str(socket_path))
    header = header_label_from_ui(ui)
    assert header.value == docker_db.DockerDbDisplayStatus.MISSING.value