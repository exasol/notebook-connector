from typing import (
    Dict,
    Union, Tuple,
)
from unittest.mock import (
    MagicMock,
    PropertyMock,
    call,
    create_autospec,
)

import docker
import pytest
from docker.models.containers import Container

from exasol.nb_connector.container_by_ip import (
    ContainerByIp
)
from test.utils.mock_cast import mock_cast


def create_docker_client_mock(
        containers: Dict[str, Dict[str, str]]) \
        -> Tuple[
            Union[docker.DockerClient, MagicMock],
            Dict[str, Union[MagicMock, Container]]]:
    docker_client_mock: Union[MagicMock, docker.DockerClient] = create_autospec(
        docker.DockerClient
    )
    container_mocks = {container_name: create_container_mock(networks)
                       for container_name, networks in containers.items()}
    mock_cast(docker_client_mock.containers.list).return_value = container_mocks.values()
    return docker_client_mock, container_mocks


def create_container_mock(networks: Dict[str, str]) -> Union[MagicMock, Container]:
    container_mock: Union[MagicMock, Container] = create_autospec(Container)
    type(container_mock).attrs = PropertyMock(
        return_value={
            "NetworkSettings": {
                "Networks": {name: {"IPAddress": ip} for name, ip in networks.items()}
            }
        }
    )
    return container_mock


class TestSetup:
    __test__ = False

    def __init__(self, containers: Dict[str, Dict[str, str]]):
        self.docker_client_mock, self.container_mocks = create_docker_client_mock(containers)
        self.container_by_ip = ContainerByIp(
            docker_client=self.docker_client_mock
        )


def test_single_container():
    """
    Verify finding a single container with all ip addresses exposed by its networks being contained in the given whitelist.
    """
    test_setup = TestSetup(
        # each container is defined by a dict specifying its networks.
        containers={
            "matching": {"test1": "192.168.0.1", "test2": "192.168.1.1"},
            "not_matching": {"test1": "192.168.2.1", "test2": "192.168.3.1"},
        },
    )
    ip_addresses = ["192.168.4.1", "192.168.5.1", "192.168.0.1", "192.168.1.1"]

    result = test_setup.container_by_ip.find(ip_addresses)

    assert test_setup.docker_client_mock.mock_calls == [call.containers.list()]
    assert result == test_setup.container_mocks["matching"]


def test_no_matching_container():
    test_setup = TestSetup(
        containers={
            "not_matching1": {"test1": "192.168.0.1", "test2": "192.168.1.1"},
            "not_matching2": {"test1": "192.168.2.1", "test2": "192.168.3.1"},
        },
    )
    ip_addresses = ["192.168.4.1", "192.168.5.1"]

    result = test_setup.container_by_ip.find(ip_addresses)

    assert test_setup.docker_client_mock.mock_calls == [call.containers.list()]
    assert result == None


def test_multiple_containers_matching():
    test_setup = TestSetup(
        containers={
            "matching1": {"test1": "192.168.0.1", "test2": "192.168.1.1"},
            "matching2": {"test1": "192.168.2.1", "test2": "192.168.3.1"},
        }
    )
    ip_addresses = ["192.168.4.1", "192.168.5.1", "192.168.0.1", "192.168.2.1"]

    with pytest.raises(
            RuntimeError, match="Found multiple matching containers: "
    ):
        test_setup.container_by_ip.find(ip_addresses)
