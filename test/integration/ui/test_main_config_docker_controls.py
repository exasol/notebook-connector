import os
import stat
from test.integration.ui.utils.ui_utils import (
    DOCKER_DB_INACCESSIBLE,
    DOCKER_DB_MISSING,
    DOCKER_DB_READY,
    DOCKER_DB_STOPPED,
)
from urllib.parse import urlparse

import docker
import pytest
from docker.errors import DockerException
from solara import display

from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.itde_manager import (
    ItdeContainerStatus,
    bring_itde_up,
    get_itde_status,
    restart_itde,
)
from exasol.nb_connector.ui.docker import docker_action_configuration


def _configure_itde_secrets(secrets) -> None:
    secrets.save(AILabConfig.use_itde, "True")
    secrets.save(AILabConfig.itde_container, "test_container")
    secrets.save(AILabConfig.itde_network, "test_network")
    secrets.save(AILabConfig.itde_volume, "test_volume")


def _render_and_capture(
    ui, ui_screenshot, *, anchor_selector: str, parent_levels: int
) -> None:
    display(ui)
    ui_screenshot(anchor_selector=anchor_selector, parent_levels=parent_levels)


def _get_socket_path_or_fail() -> str:
    socket_path = os.getenv("DOCKER_SOCKET_PATH")
    if socket_path:
        return socket_path

    docker_host = os.getenv("DOCKER_HOST")
    if docker_host:
        parsed = urlparse(docker_host)
        if parsed.scheme == "unix" and parsed.path:
            return parsed.path
        pytest.fail(f"Unsupported DOCKER_HOST value: {docker_host}")

    pytest.fail("DOCKER_SOCKET_PATH or DOCKER_HOST is not set")


def _docker_socket_reachable(socket_path: str) -> bool:
    if not os.path.exists(socket_path):
        return False
    if not stat.S_ISSOCK(os.stat(socket_path).st_mode):
        return False
    try:
        client = docker.APIClient(base_url=f"unix://{socket_path}")
        client.ping()
        return True
    except DockerException:
        return False


def _require_docker_socket_or_fail(socket_path: str) -> None:
    if not _docker_socket_reachable(socket_path):
        pytest.fail(f"Docker socket is not reachable: {socket_path}")


def _stop_itde_container(socket_path: str, container_name: str) -> None:
    try:
        client = docker.DockerClient(base_url=f"unix://{socket_path}")
        container = client.containers.get(container_name)
        container.stop()
    except docker.errors.NotFound:
        pytest.fail(f"ITDE container not found: {container_name}")
    except DockerException as exc:
        pytest.fail(f"Failed to stop ITDE container: {exc}")


def _ensure_itde_state(
    secrets, expected_status: ItdeContainerStatus, socket_path: str
) -> None:
    status = get_itde_status(secrets)
    if status == ItdeContainerStatus.ABSENT:
        bring_itde_up(secrets)
        status = get_itde_status(secrets)

    if expected_status == ItdeContainerStatus.READY:
        _ensure_itde_ready(secrets, status)
    elif expected_status == ItdeContainerStatus.STOPPED:
        _ensure_itde_stopped(secrets, status, socket_path)


def _ensure_itde_ready(secrets, status):
    if status == ItdeContainerStatus.STOPPED:
        restart_itde(secrets)
        status = get_itde_status(secrets)
    if status != ItdeContainerStatus.READY:
        pytest.fail(f"ITDE status is {status.value}, expected READY")


def _ensure_itde_stopped(secrets, status, socket_path):
    if status == ItdeContainerStatus.STOPPED:
        restart_itde(secrets)
        status = get_itde_status(secrets)
    if ItdeContainerStatus.RUNNING in status:
        container_name = secrets.get(AILabConfig.itde_container)
        if not container_name:
            pytest.fail("ITDE container name is not set")
        _stop_itde_container(socket_path, container_name)
        status = get_itde_status(secrets)
    if status != ItdeContainerStatus.STOPPED:
        pytest.fail(f"ITDE status is {status.value}, expected STOPPED")


@pytest.fixture
def itde_secrets(secrets):
    _configure_itde_secrets(secrets)
    return secrets


@pytest.fixture
def docker_socket_path():
    socket_path = _get_socket_path_or_fail()
    _require_docker_socket_or_fail(socket_path)
    return socket_path


@pytest.fixture
def itde_ready(itde_secrets, docker_socket_path):
    _ensure_itde_state(itde_secrets, ItdeContainerStatus.READY, docker_socket_path)
    return itde_secrets


@pytest.fixture
def itde_stopped(itde_secrets, docker_socket_path):
    _ensure_itde_state(itde_secrets, ItdeContainerStatus.STOPPED, docker_socket_path)
    return itde_secrets


@pytest.fixture(autouse=True)
def _stop_itde_after_each_test(secrets):
    yield
    status = get_itde_status(secrets)
    if ItdeContainerStatus.RUNNING in status:  # type: ignore[operator]
        container_name = secrets.get(AILabConfig.itde_container)
        if not container_name:
            return
        socket_path = _get_socket_path_or_fail()
        _require_docker_socket_or_fail(socket_path)
        _stop_itde_container(socket_path, container_name)


@pytest.fixture
def itde_missing(secrets):
    secrets.save(AILabConfig.use_itde, "True")
    secrets.remove(AILabConfig.itde_container)
    secrets.remove(AILabConfig.itde_network)
    return secrets


def test_docker_db_inaccessible(solara_test, tmp_path, ui_screenshot, itde_secrets):
    ui = docker_action_configuration(itde_secrets, "/var/run/unavilable.sock")
    _render_and_capture(
        ui, ui_screenshot, anchor_selector=DOCKER_DB_INACCESSIBLE, parent_levels=2
    )


def test_use_itde_false(solara_test, tmp_path, ui_screenshot, secrets):
    ui = docker_action_configuration(secrets)
    display(ui)
    assert ui is None


def test_if_docker_host_is_set(
    solara_test, tmp_path, ui_screenshot, itde_secrets, docker_socket_path
):
    assert docker_socket_path


def test_itde_and_docker_running(
    solara_test, tmp_path, ui_screenshot, itde_ready, docker_socket_path
):
    ui = docker_action_configuration(itde_ready, docker_socket_path)
    _render_and_capture(
        ui, ui_screenshot, anchor_selector=DOCKER_DB_READY, parent_levels=2
    )


def test_itde_and_docker_stopped(
    solara_test, tmp_path, ui_screenshot, itde_stopped, docker_socket_path
):
    ui = docker_action_configuration(itde_stopped, docker_socket_path)
    _render_and_capture(
        ui, ui_screenshot, anchor_selector=DOCKER_DB_STOPPED, parent_levels=2
    )


def test_itde_and_docker_missing(
    solara_test, tmp_path, ui_screenshot, itde_missing, docker_socket_path
):
    ui = docker_action_configuration(itde_missing, docker_socket_path)
    _render_and_capture(
        ui, ui_screenshot, anchor_selector=DOCKER_DB_MISSING, parent_levels=2
    )
