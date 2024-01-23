from exasol_integration_test_docker_environment.lib.docker import (  # type: ignore
    ContextDockerClient,
)
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
from exasol.secret_store import Secrets
from exasol.itde_manager import (
    bring_itde_up,
    is_itde_running,
    start_itde,
    take_itde_down,
)

DB_NETWORK_NAME = "db_network_DemoDb"

DB_VOLUME_NAME = "db_container_DemoDb_volume"

DB_CONTAINER_NAME = "db_container_DemoDb"


def remove_itde():
    remove_docker_container([DB_CONTAINER_NAME])
    remove_docker_networks([DB_NETWORK_NAME])
    remove_docker_volumes([DB_VOLUME_NAME])


def stop_itde(conf: Secrets):
    container_name = conf.get(AILabConfig.itde_container)
    with ContextDockerClient() as docker_client:
        container = docker_client.containers.get(container_name)
        container.stop()


def test_bring_itde_up(secrets):
    secrets.save(AILabConfig.mem_size, "2")
    secrets.save(AILabConfig.disk_size, "4")

    try:
        bring_itde_up(secrets)
        assert secrets.get(AILabConfig.itde_container) == DB_CONTAINER_NAME
        assert secrets.get(AILabConfig.itde_volume) == DB_VOLUME_NAME
        assert secrets.get(AILabConfig.itde_network) == DB_NETWORK_NAME
        assert secrets.get(AILabConfig.db_host_name) == secrets.get(AILabConfig.bfs_host_name)
        assert secrets.get(AILabConfig.db_user) == "sys"
        assert secrets.get(AILabConfig.db_password) == "exasol"
        assert secrets.get(AILabConfig.db_encryption) == "True"
        assert secrets.get(AILabConfig.db_port) == "8563"
        assert secrets.get(AILabConfig.bfs_service) == "bfsdefault"
        assert secrets.get(AILabConfig.bfs_bucket) == "default"
        assert secrets.get(AILabConfig.bfs_encryption) == "False"
        assert secrets.get(AILabConfig.bfs_user) == "w"
        assert secrets.get(AILabConfig.bfs_password) == "write"
        assert secrets.get(AILabConfig.bfs_port) == "2580"
    finally:
        remove_itde()


def test_itde_exists_and_running(secrets):
    secrets.save(AILabConfig.mem_size, "2")
    secrets.save(AILabConfig.disk_size, "4")

    try:
        bring_itde_up(secrets)
        itde_exists, itde_running = is_itde_running(secrets)
        assert itde_exists
        assert itde_running
    finally:
        remove_itde()


def test_itde_neither_exists_nor_running(secrets):
    remove_itde()
    itde_exists, itde_running = is_itde_running(secrets)
    assert not itde_exists
    assert not itde_running


def test_itde_exists_not_running(secrets):
    secrets.save(AILabConfig.mem_size, "2")
    secrets.save(AILabConfig.disk_size, "4")

    try:
        bring_itde_up(secrets)
        stop_itde(secrets)
        itde_exists, itde_running = is_itde_running(secrets)
        assert itde_exists
        assert not itde_running
    finally:
        remove_itde()


def test_itde_start(secrets):
    secrets.save(AILabConfig.mem_size, "2")
    secrets.save(AILabConfig.disk_size, "4")

    try:
        bring_itde_up(secrets)
        stop_itde(secrets)
        start_itde(secrets)
        itde_exists, itde_running = is_itde_running(secrets)
        assert itde_exists
        assert itde_running
    finally:
        remove_itde()


def test_take_itde_down(secrets):
    secrets.save(AILabConfig.mem_size, "2")
    secrets.save(AILabConfig.disk_size, "4")

    try:
        bring_itde_up(secrets)
        take_itde_down(secrets)
        assert secrets.get(AILabConfig.itde_container) is None
        assert secrets.get(AILabConfig.itde_volume) is None
        assert secrets.get(AILabConfig.itde_network) is None
        assert secrets.get(AILabConfig.db_host_name) is None
        assert secrets.get(AILabConfig.bfs_host_name) is None
        assert secrets.get(AILabConfig.db_user) is None
        assert secrets.get(AILabConfig.db_password) is None
        assert secrets.get(AILabConfig.db_encryption) is None
        assert secrets.get(AILabConfig.db_port) is None
        assert secrets.get(AILabConfig.bfs_service) is None
        assert secrets.get(AILabConfig.bfs_bucket) is None
        assert secrets.get(AILabConfig.bfs_encryption) is None
        assert secrets.get(AILabConfig.bfs_user) is None
        assert secrets.get(AILabConfig.bfs_password) is None
        assert secrets.get(AILabConfig.bfs_port) is None
    finally:
        remove_itde()


def test_take_itde_down_is_not_itde_running(secrets):
    secrets.save(AILabConfig.mem_size, "2")
    secrets.save(AILabConfig.disk_size, "4")
    try:
        bring_itde_up(secrets)
        take_itde_down(secrets)
        itde_exists, itde_running = is_itde_running(secrets)
        assert not itde_exists
        assert not itde_running
    finally:
        remove_itde()
