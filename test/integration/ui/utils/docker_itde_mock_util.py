"""Utilities for mocking the ITDE and Docker behavior in UI tests."""

from __future__ import annotations

import docker

from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.itde_manager import ItdeContainerStatus


class ItdeMockState:
    """Track the mocked ITDE container status for a test run."""

    def __init__(self) -> None:
        self.status = ItdeContainerStatus.ABSENT


class _FakeContainer:
    """Minimal container stub used by the mocked Docker client."""

    def stop(self) -> None:
        return None


class _FakeContainerManager:
    """Container manager stub that returns a fake container."""

    def get(self, _name: str) -> _FakeContainer:
        return _FakeContainer()


class _FakeDockerClient:
    """Minimal Docker client stub with a containers manager and close()."""

    def __init__(self) -> None:
        self.containers = _FakeContainerManager()

    def close(self) -> None:
        return None


def apply_itde_docker_mocks(monkeypatch) -> ItdeMockState:
    """Patch ITDE helpers and Docker client to use fakes for UI tests."""
    state = ItdeMockState()

    def _fake_get_itde_status(_secrets):
        return state.status

    def _fake_bring_itde_up(_secrets):
        _secrets.save(AILabConfig.itde_container, "mock-itde")
        _secrets.save(AILabConfig.itde_network, "mock-net")
        state.status = ItdeContainerStatus.READY

    def _fake_restart_itde(_secrets):
        state.status = ItdeContainerStatus.READY

    def _fake_take_itde_down(_secrets):
        state.status = ItdeContainerStatus.ABSENT

    # Patch itde_manager module (used by UI code).
    monkeypatch.setattr(
        "exasol.nb_connector.itde_manager.get_itde_status", _fake_get_itde_status
    )
    monkeypatch.setattr(
        "exasol.nb_connector.itde_manager.bring_itde_up", _fake_bring_itde_up
    )
    monkeypatch.setattr(
        "exasol.nb_connector.itde_manager.restart_itde", _fake_restart_itde
    )
    monkeypatch.setattr(
        "exasol.nb_connector.itde_manager.take_itde_down", _fake_take_itde_down
    )

    # Patch UI module imports (docker_db imports these directly).
    monkeypatch.setattr(
        "exasol.nb_connector.ui.docker.docker_db.get_itde_status", _fake_get_itde_status
    )
    monkeypatch.setattr(
        "exasol.nb_connector.ui.docker.docker_db.bring_itde_up", _fake_bring_itde_up
    )
    monkeypatch.setattr(
        "exasol.nb_connector.ui.docker.docker_db.restart_itde", _fake_restart_itde
    )
    monkeypatch.setattr(
        "exasol.nb_connector.ui.docker.docker_db.take_itde_down", _fake_take_itde_down
    )

    # Mock Docker client for  usage in the test module.
    monkeypatch.setattr(docker, "from_env", lambda: _FakeDockerClient())

    return state
