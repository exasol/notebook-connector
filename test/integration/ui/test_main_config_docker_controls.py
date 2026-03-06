"""UI tests for the Docker-DB controls in the main config screen."""

from test.integration.ui.utils.docker_itde_mock_util import apply_itde_docker_mocks
from test.integration.ui.utils.ui_utils import (
    DOCKER_DB_CREATE_START_BUTTON,
    DOCKER_DB_DISCONNECTED,
    DOCKER_DB_INACCESSIBLE,
    DOCKER_DB_MISSING,
    DOCKER_DB_READY,
    DOCKER_DB_RECREATE_START_BUTTON,
    DOCKER_DB_START_BUTTON,
    DOCKER_DB_STOPPED,
)

import pytest
from solara import display

from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.itde_manager import ItdeContainerStatus
from exasol.nb_connector.ui.docker import docker_action_configuration


@pytest.fixture
def itde_secrets(secrets):
    """Return secrets with ITDE enabled for this test."""
    secrets.save(AILabConfig.use_itde, "True")
    return secrets


@pytest.fixture(autouse=True)
def _mock_itde_manager_and_docker(monkeypatch):
    """Mock ITDE and Docker calls so tests do not use real services."""
    return apply_itde_docker_mocks(monkeypatch)


def _set_itde_container_and_network(secrets) -> None:
    """Set standard ITDE container and network values for tests."""
    secrets.save(AILabConfig.itde_container, "mock-itde")
    secrets.save(AILabConfig.itde_network, "mock-net")


@pytest.fixture
def itde_ready(itde_secrets, _mock_itde_manager_and_docker):
    """Return secrets set to a mocked READY ITDE state."""
    state = _mock_itde_manager_and_docker
    state.status = ItdeContainerStatus.READY
    _set_itde_container_and_network(itde_secrets)
    return itde_secrets


@pytest.fixture
def itde_stopped(itde_secrets, _mock_itde_manager_and_docker):
    """Return secrets set to a mocked STOPPED ITDE state."""
    state = _mock_itde_manager_and_docker
    state.status = ItdeContainerStatus.STOPPED
    _set_itde_container_and_network(itde_secrets)
    return itde_secrets


@pytest.fixture
def itde_missing(secrets, _mock_itde_manager_and_docker):
    """Return secrets with no ITDE container to simulate missing state."""
    state = _mock_itde_manager_and_docker
    state.status = ItdeContainerStatus.ABSENT
    secrets.save(AILabConfig.use_itde, "True")
    secrets.remove(AILabConfig.itde_container)
    secrets.remove(AILabConfig.itde_network)
    return secrets


@pytest.fixture
def itde_disconnected(itde_secrets, _mock_itde_manager_and_docker):
    """Return secrets set to a mocked RUNNING ITDE state without visibility."""
    state = _mock_itde_manager_and_docker
    state.status = ItdeContainerStatus.RUNNING
    _set_itde_container_and_network(itde_secrets)
    return itde_secrets


def _click_button_and_wait_ready(
    page_session,
    button_selector: str,
    *,
    ready_selector: str = DOCKER_DB_READY,
    timeout_ms: int = 60000,
) -> None:
    """Click a button and wait for the ready message to appear."""
    button = page_session.locator(button_selector)
    button.wait_for()
    button.click()
    page_session.locator(ready_selector).wait_for(timeout=timeout_ms)


def _create_docker_socket(tmp_path) -> str:
    """Create a temporary socket file to simulate a mounted Docker socket."""
    socket_path = tmp_path / "docker.sock"
    socket_path.touch()
    return str(socket_path)


def test_docker_db_inaccessible(solara_test, tmp_path, ui_screenshot, itde_secrets):
    """Show UI state when Docker socket is not reachable."""
    ui = docker_action_configuration(itde_secrets, "/var/run/unavilable.sock")
    assert ui is not None
    display(ui)
    ui_screenshot(anchor_selector=DOCKER_DB_INACCESSIBLE, parent_levels=2)


def test_use_itde_false(solara_test, tmp_path, ui_screenshot, secrets):
    """Ensure UI is hidden when ITDE use is disabled."""
    ui = docker_action_configuration(secrets)
    display(ui)
    assert ui is None


def test_itde_and_docker_running(solara_test, tmp_path, ui_screenshot, itde_ready):
    """Show UI state when ITDE is running and Docker is ready."""
    socket_path = _create_docker_socket(tmp_path)
    ui = docker_action_configuration(itde_ready, socket_path)
    assert ui is not None
    display(ui)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_itde_and_docker_stopped(solara_test, tmp_path, ui_screenshot, itde_stopped):
    """Show UI state when ITDE exists but is stopped."""
    socket_path = _create_docker_socket(tmp_path)
    ui = docker_action_configuration(itde_stopped, socket_path)
    assert ui is not None
    display(ui)
    ui_screenshot(anchor_selector=DOCKER_DB_STOPPED, parent_levels=2)


def test_itde_and_docker_missing(solara_test, tmp_path, ui_screenshot, itde_missing):
    """Show UI state when ITDE is missing."""
    socket_path = _create_docker_socket(tmp_path)
    ui = docker_action_configuration(itde_missing, socket_path)
    assert ui is not None
    display(ui)
    ui_screenshot(anchor_selector=DOCKER_DB_MISSING, parent_levels=2)


def test_start_docker_db_button_creates_itde(
    solara_test, page_session, itde_missing, ui_screenshot, tmp_path
):
    """Click create/start and wait until ITDE becomes ready."""
    socket_path = _create_docker_socket(tmp_path)
    ui = docker_action_configuration(itde_missing, socket_path)
    assert ui is not None
    display(ui)
    _click_button_and_wait_ready(page_session, DOCKER_DB_CREATE_START_BUTTON)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_restart_docker_db_button_recreates_itde(
    solara_test, page_session, itde_ready, ui_screenshot, tmp_path
):
    """Click restart to recreate ITDE and verify readiness."""
    socket_path = _create_docker_socket(tmp_path)
    ui = docker_action_configuration(itde_ready, socket_path)
    assert ui is not None
    display(ui)
    _click_button_and_wait_ready(page_session, DOCKER_DB_RECREATE_START_BUTTON)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_start_docker_db_button_starts_itde(
    solara_test, page_session, itde_stopped, ui_screenshot, tmp_path
):
    """Click start to bring ITDE to ready state."""
    socket_path = _create_docker_socket(tmp_path)
    ui = docker_action_configuration(itde_stopped, socket_path)
    assert ui is not None
    display(ui)
    _click_button_and_wait_ready(page_session, DOCKER_DB_START_BUTTON)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_itde_and_docker_disconnected(
    solara_test, tmp_path, ui_screenshot, itde_disconnected
):
    """Show UI state when ITDE runs but the container is not connected."""
    socket_path = _create_docker_socket(tmp_path)
    ui = docker_action_configuration(itde_disconnected, socket_path)
    assert ui is not None
    display(ui)
    ui_screenshot(anchor_selector=DOCKER_DB_DISCONNECTED, parent_levels=2)
