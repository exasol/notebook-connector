import logging
from collections.abc import Iterator
from unittest import mock

import pytest
from exasol_integration_test_docker_environment.lib.models.data.container_info import (
    ContainerInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.database_info import (
    DatabaseInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.docker_network_info import (
    DockerNetworkInfo,
)
from exasol_integration_test_docker_environment.lib.models.data.environment_info import (
    EnvironmentInfo,
)
from exasol_integration_test_docker_environment.lib.test_environment.ports import Ports

from exasol.nb_connector.ai_lab_config import Accelerator
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.itde_manager import (
    ENVIRONMENT_NAME,
    NAME_SERVER_ADDRESS,
    TEST_DB_VERSION_ENV_VAR,
    ItdeContainerStatus,
    bring_itde_up,
    take_itde_down,
)

TEST_CONTAINER_NAME = "the_new_container"
TEST_VOLUME_NAME = "the_new_volume"
TEST_NETWORK_NAME = "the_new_network"
TEST_DB_HOST = "the_host"
TEST_DB_PORT = 8888
TEST_BFS_PORT = 6666


@pytest.fixture
def env_info() -> EnvironmentInfo:
    net_info = DockerNetworkInfo(TEST_NETWORK_NAME, "127.0.0.0", "2.3.4.5")
    container_info = ContainerInfo(
        TEST_CONTAINER_NAME, "6.7.8.9", [], net_info, TEST_VOLUME_NAME
    )
    ports = Ports(TEST_DB_PORT, TEST_BFS_PORT)
    db_info = DatabaseInfo(TEST_DB_HOST, ports, False, container_info)
    return EnvironmentInfo("env_name", "env_type", db_info, None, net_info)


@pytest.fixture
def db_image_version(monkeypatch) -> Iterator[str]:
    mocked_db_version = "8.31.0"
    monkeypatch.setenv(TEST_DB_VERSION_ENV_VAR, mocked_db_version)
    yield mocked_db_version
    monkeypatch.delenv(TEST_DB_VERSION_ENV_VAR)


@mock.patch("exasol_integration_test_docker_environment.lib.api.spawn_test_environment")
def test_bring_itde_up(mock_spawn_env, secrets, env_info, db_image_version):
    mock_spawn_env.return_value = (env_info, None)

    secrets.save(CKey.mem_size, "4")
    secrets.save(CKey.disk_size, "10")

    bring_itde_up(secrets)

    assert mock_spawn_env.mock_calls == [
        mock.call(
            environment_name=ENVIRONMENT_NAME,
            nameserver=(NAME_SERVER_ADDRESS,),
            db_mem_size="4 GiB",
            db_disk_size="10 GiB",
            docker_db_image_version=db_image_version,
            docker_runtime=None,
            docker_environment_variable=(),
            additional_db_parameter=("-etlCheckCertsDefault=0",),
            log_level=logging.getLevelName(logging.INFO),
        )
    ]

    assert secrets.get(CKey.itde_container) == TEST_CONTAINER_NAME
    assert secrets.get(CKey.itde_volume) == TEST_VOLUME_NAME
    assert secrets.get(CKey.itde_network) == TEST_NETWORK_NAME
    assert secrets.get(CKey.db_host_name) == TEST_DB_HOST
    assert secrets.get(CKey.bfs_host_name) == TEST_DB_HOST
    assert int(secrets.get(CKey.db_port)) == TEST_DB_PORT
    assert int(secrets.get(CKey.bfs_port)) == TEST_BFS_PORT
    assert secrets.get(CKey.db_user) == "sys"
    assert secrets.get(CKey.db_password) == "exasol"
    assert secrets.get(CKey.db_encryption) == "True"
    assert secrets.get(CKey.bfs_service) == "bfsdefault"
    assert secrets.get(CKey.bfs_bucket) == "default"
    assert secrets.get(CKey.bfs_encryption) == "False"
    assert secrets.get(CKey.bfs_user) == "w"
    assert secrets.get(CKey.bfs_password) == "write"


@mock.patch("exasol_integration_test_docker_environment.lib.api.spawn_test_environment")
@pytest.mark.parametrize(
    "accelerator, expected_docker_runtime, expected_docker_environment_variable, expected_additional_db_parameter",
    [
        (Accelerator.none.value, None, (), ("-etlCheckCertsDefault=0",)),
        (
            Accelerator.nvidia.value,
            "nvidia",
            ("NVIDIA_VISIBLE_DEVICES=all",),
            (
                "-etlCheckCertsDefault=0",
                "-enableAcceleratorDeviceDetection=1",
            ),
        ),
    ],
)
def test_bring_itde_up_with_accelerator(
    mock_spawn_env,
    secrets,
    env_info,
    db_image_version,
    accelerator,
    expected_docker_runtime,
    expected_docker_environment_variable,
    expected_additional_db_parameter,
):
    mock_spawn_env.return_value = (env_info, None)

    secrets.save(CKey.accelerator, accelerator)

    bring_itde_up(secrets)

    assert mock_spawn_env.mock_calls == [
        mock.call(
            environment_name=ENVIRONMENT_NAME,
            nameserver=(NAME_SERVER_ADDRESS,),
            db_mem_size="4 GiB",
            db_disk_size="10 GiB",
            docker_db_image_version=db_image_version,
            docker_runtime=expected_docker_runtime,
            docker_environment_variable=expected_docker_environment_variable,
            additional_db_parameter=expected_additional_db_parameter,
            log_level=logging.getLevelName(logging.INFO),
        )
    ]


@mock.patch(
    "exasol_integration_test_docker_environment.lib.docker.container.utils.remove_docker_container"
)
@mock.patch(
    "exasol_integration_test_docker_environment.lib.docker.volumes.utils.remove_docker_volumes"
)
@mock.patch(
    "exasol_integration_test_docker_environment.lib.docker.networks.utils.remove_docker_networks"
)
def test_take_itde_down(mock_util1, mock_util2, mock_util3, secrets):
    secrets.save(CKey.itde_container, TEST_CONTAINER_NAME)
    secrets.save(CKey.itde_volume, TEST_VOLUME_NAME)
    secrets.save(CKey.itde_network, TEST_NETWORK_NAME)

    take_itde_down(secrets)

    assert secrets.get(CKey.itde_container) is None
    assert secrets.get(CKey.itde_volume) is None
    assert secrets.get(CKey.itde_network) is None
    assert secrets.get(CKey.db_host_name) is None
    assert secrets.get(CKey.bfs_host_name) is None
    assert secrets.get(CKey.db_user) is None
    assert secrets.get(CKey.db_password) is None
    assert secrets.get(CKey.db_encryption) is None
    assert secrets.get(CKey.db_port) is None
    assert secrets.get(CKey.bfs_service) is None
    assert secrets.get(CKey.bfs_bucket) is None
    assert secrets.get(CKey.bfs_encryption) is None
    assert secrets.get(CKey.bfs_user) is None
    assert secrets.get(CKey.bfs_password) is None
    assert secrets.get(CKey.bfs_port) is None


@pytest.mark.parametrize(
    "status",
    [
        ItdeContainerStatus.RUNNING,
        ItdeContainerStatus.READY,
    ],
)
def test_status_running(status):
    assert ItdeContainerStatus.RUNNING in status


@pytest.mark.parametrize(
    "status",
    [
        ItdeContainerStatus.ABSENT,
        ItdeContainerStatus.STOPPED,
        ItdeContainerStatus.VISIBLE,
    ],
)
def test_status_not_running(status):
    assert ItdeContainerStatus.RUNNING not in status


@pytest.mark.parametrize(
    "status",
    [
        ItdeContainerStatus.VISIBLE,
        ItdeContainerStatus.READY,
    ],
)
def test_status_visible(status):
    assert ItdeContainerStatus.VISIBLE in status


@pytest.mark.parametrize(
    "status",
    [
        ItdeContainerStatus.ABSENT,
        ItdeContainerStatus.STOPPED,
        ItdeContainerStatus.RUNNING,
    ],
)
def test_status_not_visible(status):
    assert ItdeContainerStatus.VISIBLE not in status
