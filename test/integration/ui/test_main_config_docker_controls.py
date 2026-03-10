"""UI tests for the Docker-DB controls in the main config screen."""

from datetime import timedelta
from test.integration.ui.utils.docker_itde_mock_util import patch_itde_manager
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
from test.utils.time_util import milliseconds

import pytest
import solara

import exasol.nb_connector.ui.docker as ui
from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.itde_manager import ItdeContainerStatus


@pytest.fixture
def itde_secrets(secrets):
    """Return secrets with ITDE enabled for this test."""
    secrets.save(AILabConfig.use_itde, "True")
    return secrets


@pytest.fixture(autouse=True) # why autouse?
# def _mock_itde_manager_and_docker(monkeypatch):
def itde_manager_mock(monkeypatch):
    """Mock ITDE and Docker calls so tests do not use real services."""
    return patch_itde_manager(monkeypatch)


def _set_itde_container_and_network(secrets) -> None:
    """Set standard ITDE container and network values for tests."""
    secrets.save(AILabConfig.itde_container, "mock-itde")
    secrets.save(AILabConfig.itde_network, "mock-net")


@pytest.fixture
def itde_ready(itde_secrets, itde_manager_mock):
    """Return secrets set to a mocked READY ITDE state."""
    itde_manager_mock.state = ItdeContainerStatus.READY
    _set_itde_container_and_network(itde_secrets)
    return itde_secrets


@pytest.fixture
def itde_stopped(itde_secrets, itde_manager_mock):
    """Return secrets set to a mocked STOPPED ITDE state."""
    itde_manager_mock.state = ItdeContainerStatus.STOPPED
    _set_itde_container_and_network(itde_secrets)
    return itde_secrets


@pytest.fixture
def itde_missing(secrets, itde_manager_mock):
    """Return secrets with no ITDE container to simulate missing state."""
    itde_manager_mock.state = ItdeContainerStatus.ABSENT
    secrets.save(AILabConfig.use_itde, "True")
    secrets.remove(AILabConfig.itde_container)
    secrets.remove(AILabConfig.itde_network)
    return secrets


@pytest.fixture
def itde_disconnected(itde_secrets, itde_manager_mock):
    """Return secrets set to a mocked RUNNING ITDE state without visibility."""
    itde_manager_mock.state = ItdeContainerStatus.RUNNING
    _set_itde_container_and_network(itde_secrets)
    return itde_secrets


@pytest.fixture
def socket_mock(tmp_path) -> str:
    """Return a temporary socket path to simulate a mounted Docker socket."""
    socket_path = tmp_path / "docker.sock"
    socket_path.touch()
    return str(socket_path)


def _click_button_and_wait_ready(
    page_session,
    button_selector: str,
    *,
    ready_selector: str = DOCKER_DB_READY,
    timeout: timedelta = timedelta(seconds=60),
) -> None:
    """Click a button and wait for the ready message to appear."""
    button = page_session.locator(button_selector)
    button.wait_for()
    button.click()
    page_session.locator(ready_selector).wait_for(timeout=milliseconds(timeout))


def test_docker_db_inaccessible(solara_test, ui_screenshot, itde_secrets):
    """Show UI state when Docker socket is not reachable."""
    widget = ui.manage_docker_db(itde_secrets, "/var/run/unavilable.sock")
    assert widget is not None
    solara.display(widget)
    ui_screenshot(anchor_selector=DOCKER_DB_INACCESSIBLE, parent_levels=2)


def test_use_itde_false(solara_test, secrets):
    """Ensure UI is hidden when ITDE use is disabled."""
    widget = ui.manage_docker_db(secrets)
    solara.display(widget)
    assert widget is None


def test_itde_and_docker_running(solara_test, socket_mock, ui_screenshot, itde_ready):
    """Show UI state when ITDE is running and Docker is ready."""
    widget = ui.manage_docker_db(itde_ready, socket_mock)
    assert widget is not None
    solara.display(widget)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_itde_and_docker_stopped(solara_test, socket_mock, ui_screenshot, itde_stopped):
    """Show UI state when ITDE exists but is stopped."""
    widget = ui.manage_docker_db(itde_stopped, socket_mock)
    assert widget is not None
    solara.display(widget)
    ui_screenshot(anchor_selector=DOCKER_DB_STOPPED, parent_levels=2)


def test_itde_and_docker_missing(solara_test, socket_mock, ui_screenshot, itde_missing):
    """Show UI state when ITDE is missing."""
    widget = ui.manage_docker_db(itde_missing, socket_mock)
    assert widget is not None
    solara.display(widget)
    ui_screenshot(anchor_selector=DOCKER_DB_MISSING, parent_levels=2)


def test_start_docker_db_button_creates_itde(
    solara_test, page_session, itde_missing, ui_screenshot, socket_mock
):
    """Click create/start and wait until ITDE becomes ready."""
    widget = ui.manage_docker_db(itde_missing, socket_mock)
    assert widget is not None
    solara.display(widget)
    _click_button_and_wait_ready(page_session, DOCKER_DB_CREATE_START_BUTTON)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_restart_docker_db_button_recreates_itde(
    solara_test, page_session, itde_ready, ui_screenshot, socket_mock
):
    """Click restart to recreate ITDE and verify readiness."""
    widget = ui.manage_docker_db(itde_ready, socket_mock)
    assert widget is not None
    solara.display(widget)
    _click_button_and_wait_ready(page_session, DOCKER_DB_RECREATE_START_BUTTON)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_start_docker_db_button_starts_itde(
    solara_test, page_session, itde_stopped, ui_screenshot, socket_mock
):
    """Click start to bring ITDE to ready state."""
    widget = ui.manage_docker_db(itde_stopped, socket_mock)
    assert widget is not None
    solara.display(widget)
    _click_button_and_wait_ready(page_session, DOCKER_DB_START_BUTTON)
    ui_screenshot(anchor_selector=DOCKER_DB_READY, parent_levels=2)


def test_itde_and_docker_disconnected(
    solara_test, socket_mock, ui_screenshot, itde_disconnected
):
    """Show UI state when ITDE runs but the container is not connected."""
    widget = ui.manage_docker_db(itde_disconnected, socket_mock)
    assert widget is not None
    solara.display(widget)
    ui_screenshot(anchor_selector=DOCKER_DB_DISCONNECTED, parent_levels=2)
