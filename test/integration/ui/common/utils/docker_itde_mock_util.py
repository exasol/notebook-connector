"""Patch ITDE and Docker in UI tests."""

from unittest.mock import Mock

import docker

from exasol.nb_connector import itde_manager
from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.itde_manager import ItdeContainerStatus
from exasol.nb_connector.ui.docker import docker_db


def mock_docker_client():
    def container():
        mock = Mock()
        mock.stop.return_value = None
        return mock

    def container_manager():
        mock = Mock()
        mock.get.return_value = container()
        return mock

    client = Mock()
    client.containers = container_manager()
    client.close.return_value = None
    return client


class ItdeManagerMock:
    def __init__(self) -> None:
        self.state = ItdeContainerStatus.ABSENT

    def get_state(self, secrets) -> ItdeContainerStatus:
        return self.state

    def bring_up(self, secrets) -> None:
        secrets.save(AILabConfig.itde_container, "mock-itde")
        secrets.save(AILabConfig.itde_network, "mock-net")
        self.state = ItdeContainerStatus.READY

    def restart(self, secrets) -> None:
        self.state = ItdeContainerStatus.READY

    def take_down(self, secrets) -> None:
        self.state = ItdeContainerStatus.ABSENT


def patch_itde_manager(monkeypatch) -> ItdeManagerMock:
    """Patch ITDE and Docker client to use mocks in UI tests."""

    mock = ItdeManagerMock()
    # Patch modules itde_manager (used by UI code) and imports of docker_db
    for module in (itde_manager, docker_db):
        monkeypatch.setattr(module, "get_itde_status", mock.get_state)
        monkeypatch.setattr(module, "bring_itde_up", mock.bring_up)
        monkeypatch.setattr(module, "restart_itde", mock.restart)
        monkeypatch.setattr(module, "take_itde_down", mock.take_down)

    # Patch Docker client for usage in the test module.
    monkeypatch.setattr(docker, "from_env", mock_docker_client)

    return mock
