from exasol_integration_test_docker_environment.lib.docker.container.utils import (
    remove_docker_container,  # type: ignore
)
from exasol_integration_test_docker_environment.lib.docker.networks.utils import (
    remove_docker_networks,  # type: ignore
)
from exasol_integration_test_docker_environment.lib.docker.volumes.utils import (
    remove_docker_volumes,  # type: ignore
)

from exasol.ai_lab_config import AILabConfig
from exasol.itde_manager import (
    bring_itde_up,
    is_itde_running,
    take_itde_down,
)

DB_NETWORK_NAME = "db_network_DemoDb"

DB_VOLUME_NAME = "db_container_DemoDb_volume"

DB_CONTAINER_NAME = "db_container_DemoDb"


def remove_itde():
    remove_docker_container([DB_CONTAINER_NAME])
    remove_docker_networks([DB_NETWORK_NAME])
    remove_docker_volumes([DB_VOLUME_NAME])


def test_bring_itde_up(secrets):
    secrets.save(AILabConfig.mem_size.value, "2")
    secrets.save(AILabConfig.disk_size.value, "4")

    try:
        bring_itde_up(secrets)
        assert secrets.get(AILabConfig.itde_container) == DB_CONTAINER_NAME
        assert secrets.get(AILabConfig.itde_volume) == DB_VOLUME_NAME
        assert secrets.get(AILabConfig.itde_network) == DB_NETWORK_NAME
        assert secrets.get(AILabConfig.db_host_name.value) == secrets.get(
            AILabConfig.bfs_host_name.value
        )
        assert secrets.get(AILabConfig.db_user.value) == "sys"
        assert secrets.get(AILabConfig.db_password.value) == "exasol"
        assert secrets.get(AILabConfig.db_encryption.value) == "True"
        assert secrets.get(AILabConfig.db_port.value) == "8563"
        assert secrets.get(AILabConfig.bfs_service.value) == "bfsdefault"
        assert secrets.get(AILabConfig.bfs_bucket.value) == "default"
        assert secrets.get(AILabConfig.bfs_encryption.value) == "False"
        assert secrets.get(AILabConfig.bfs_user.value) == "w"
        assert secrets.get(AILabConfig.bfs_password.value) == "write"
        assert secrets.get(AILabConfig.bfs_port.value) == "2580"
    finally:
        remove_itde()


def test_is_itde_running(secrets):
    secrets.save(AILabConfig.mem_size.value, "2")
    secrets.save(AILabConfig.disk_size.value, "4")

    try:
        bring_itde_up(secrets)
        itde_running = is_itde_running(secrets)
        assert itde_running is True
    finally:
        remove_itde()


def test_is_not_itde_running(secrets):
    remove_itde()
    itde_running = is_itde_running(secrets)
    assert itde_running is False


def test_take_itde_down(secrets):
    secrets.save(AILabConfig.mem_size.value, "2")
    secrets.save(AILabConfig.disk_size.value, "4")

    try:
        bring_itde_up(secrets)
        take_itde_down(secrets)
        assert secrets.get(AILabConfig.itde_container) is None
        assert secrets.get(AILabConfig.itde_volume) is None
        assert secrets.get(AILabConfig.itde_network) is None
        assert secrets.get(AILabConfig.db_host_name.value) is None
        assert secrets.get(AILabConfig.bfs_host_name.value) is None
        assert secrets.get(AILabConfig.db_user.value) is None
        assert secrets.get(AILabConfig.db_password.value) is None
        assert secrets.get(AILabConfig.db_encryption.value) is None
        assert secrets.get(AILabConfig.db_port.value) is None
        assert secrets.get(AILabConfig.bfs_service.value) is None
        assert secrets.get(AILabConfig.bfs_bucket.value) is None
        assert secrets.get(AILabConfig.bfs_encryption.value) is None
        assert secrets.get(AILabConfig.bfs_user.value) is None
        assert secrets.get(AILabConfig.bfs_password.value) is None
        assert secrets.get(AILabConfig.bfs_port.value) is None
    finally:
        remove_itde()


def test_take_itde_down_is_not_itde_running(secrets):
    secrets.save(AILabConfig.mem_size.value, "2")
    secrets.save(AILabConfig.disk_size.value, "4")
    try:
        bring_itde_up(secrets)
        take_itde_down(secrets)
        itde_running = is_itde_running(secrets)
        assert itde_running is False
    finally:
        remove_itde()
