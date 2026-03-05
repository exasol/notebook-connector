from test.integration.ui.utils.ui_utils import (
    DOCKER_DB_CREATE_START_BUTTON,
    DOCKER_DB_INACCESSIBLE,
    DOCKER_DB_MISSING,
    DOCKER_DB_READY,
    DOCKER_DB_RECREATE_START_BUTTON,
    DOCKER_DB_START_BUTTON,
    DOCKER_DB_STOPPED,
)

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
    take_itde_down,
)
from exasol.nb_connector.ui.docker import docker_action_configuration


def _configure_itde_secrets(secrets) -> None:
    secrets.save(AILabConfig.use_itde, "True")


def _stop_itde_container(container_name: str) -> None:
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.stop()
    except docker.errors.NotFound:
        pytest.fail(f"ITDE container not found: {container_name}")
    except DockerException as exc:
        pytest.fail(f"Failed to stop ITDE container: {exc}")


def _ensure_itde_ready(secrets, status: ItdeContainerStatus) -> None:
    if status == ItdeContainerStatus.STOPPED:
        restart_itde(secrets)
        status = get_itde_status(secrets)
    if status != ItdeContainerStatus.READY:
        pytest.fail(f"ITDE status is {status.value}, expected READY")


def _ensure_itde_stopped(secrets, status: ItdeContainerStatus) -> None:
    if status == ItdeContainerStatus.STOPPED:
        restart_itde(secrets)
        status = get_itde_status(secrets)
    if ItdeContainerStatus.RUNNING in status:
        container_name = secrets.get(AILabConfig.itde_container)
        if not container_name:
            pytest.fail("ITDE container name is not set")
        _stop_itde_container(container_name)
        status = get_itde_status(secrets)
    if status != ItdeContainerStatus.STOPPED:
        pytest.fail(f"ITDE status is {status.value}, expected STOPPED")


def _ensure_itde_state(secrets, expected_status: ItdeContainerStatus) -> None:
    status = get_itde_status(secrets)
    if status == ItdeContainerStatus.ABSENT:
        bring_itde_up(secrets)
        status = get_itde_status(secrets)

    if expected_status == ItdeContainerStatus.READY:
        _ensure_itde_ready(secrets, status)
        return

    if expected_status == ItdeContainerStatus.STOPPED:
        _ensure_itde_stopped(secrets, status)


@pytest.fixture
def itde_secrets(secrets):
    _configure_itde_secrets(secrets)
    return secrets


@pytest.fixture
def itde_ready(itde_secrets):
    _ensure_itde_state(itde_secrets, ItdeContainerStatus.READY)
    return itde_secrets


@pytest.fixture
def itde_stopped(itde_secrets):
    _ensure_itde_state(itde_secrets, ItdeContainerStatus.STOPPED)
    return itde_secrets


@pytest.fixture(autouse=True)
def _stop_itde_after_each_test(secrets):
    yield
    take_itde_down(secrets)


@pytest.fixture
def itde_missing(secrets):
    secrets.save(AILabConfig.use_itde, "True")
    secrets.remove(AILabConfig.itde_container)
    secrets.remove(AILabConfig.itde_network)
    return secrets


def _click_button_and_wait_ready(
    page_session,
    button_selector: str,
    *,
    ready_selector: str = DOCKER_DB_READY,
    timeout_ms: int = 60000,
) -> None:
    button = page_session.locator(button_selector)
    button.wait_for()
    button.click()
    page_session.locator(ready_selector).wait_for(timeout=timeout_ms)


def test_docker_db_inaccessible(solara_test, tmp_path, ui_screenshot, itde_secrets):
    ui = docker_action_configuration(itde_secrets, "/var/run/unavilable.sock")
    assert ui is not None
    display(ui)
    ui_screenshot(anchor_selector=DOCKER_DB_INACCESSIBLE, parent_levels=2)


def test_use_itde_false(solara_test, tmp_path, ui_screenshot, secrets):
    ui = docker_action_configuration(secrets)
    display(ui)
    assert ui is None


def test_itde_and_docker_running(solara_test, tmp_path, ui_screenshot, itde_ready):
    ui = docker_action_configuration(itde_ready)
    assert ui is not None
    display(ui)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_itde_and_docker_stopped(solara_test, tmp_path, ui_screenshot, itde_stopped):
    ui = docker_action_configuration(itde_stopped)
    assert ui is not None
    display(ui)
    ui_screenshot(anchor_selector=DOCKER_DB_STOPPED, parent_levels=2)


def test_itde_and_docker_missing(solara_test, tmp_path, ui_screenshot, itde_missing):
    ui = docker_action_configuration(itde_missing)
    assert ui is not None
    display(ui)
    ui_screenshot(anchor_selector=DOCKER_DB_MISSING, parent_levels=2)


def test_start_docker_db_button_creates_itde(
    solara_test, page_session, itde_missing, ui_screenshot
):
    ui = docker_action_configuration(itde_missing)
    assert ui is not None
    display(ui)
    _click_button_and_wait_ready(page_session, DOCKER_DB_CREATE_START_BUTTON)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_restart_docker_db_button_recreates_itde(
    solara_test, page_session, itde_ready, ui_screenshot
):
    ui = docker_action_configuration(itde_ready)
    assert ui is not None
    display(ui)
    _click_button_and_wait_ready(page_session, DOCKER_DB_RECREATE_START_BUTTON)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_start_docker_db_button_starts_itde(
    solara_test, page_session, itde_stopped, ui_screenshot
):
    ui = docker_action_configuration(itde_stopped)
    assert ui is not None
    display(ui)
    _click_button_and_wait_ready(page_session, DOCKER_DB_START_BUTTON)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)
