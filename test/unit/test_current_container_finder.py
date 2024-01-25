import dataclasses
from test.utils.mock_cast import mock_cast
from typing import (
    Dict,
    List,
    Union,
)
from unittest.mock import (
    MagicMock,
    PropertyMock,
    call,
    create_autospec,
)

import docker
import ifaddr
import pytest
from docker.models.containers import Container

from exasol.current_container_finder import (
    CurrentContainerFinder,
    IPRetriever,
)


def create_ip_retriever_mock(ip_addresses: List[str]) -> Union[MagicMock, IPRetriever]:
    ip_retriever_mock: Union[MagicMock, IPRetriever] = create_autospec(IPRetriever)
    ip_mocks = [create_ip_mock(ip_address) for ip_address in ip_addresses]
    mock_cast(ip_retriever_mock.ips).return_value = ip_mocks
    return ip_retriever_mock


from typing import NewType
Network = NewType("Network", Dict[str, str])


def create_docker_client_mock(
    containers: List[Network]
) -> Union[docker.DockerClient, MagicMock]:
    docker_client_mock: Union[MagicMock, docker.DockerClient] = create_autospec(
        docker.DockerClient
    )
    container_mocks = [create_container_mock(networks) for networks in containers]
    mock_cast(docker_client_mock.containers.list).return_value = container_mocks
    return docker_client_mock


def create_ip_mock(ip_address: str) -> Union[MagicMock, ifaddr.IP]:
    ip_mock: Union[MagicMock, ifaddr.IP] = create_autospec(ifaddr.IP)
    type(ip_mock).ip = PropertyMock(return_value=ip_address)
    return ip_mock


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
    def __init__(self, containers: List[Dict[str, str]], ip_addresses: List[str]):
        self.docker_client_mock = create_docker_client_mock(containers)
        self.ip_retriever_mock = create_ip_retriever_mock(ip_addresses)
        self.current_container_finder = CurrentContainerFinder(
            docker_client=self.docker_client_mock, ip_retriever=self.ip_retriever_mock
        )


def test_single_container():
    """
    Verify finding a single container with all ip addresses exposed by its networks being contained in the given whitelist.
    """
    test_setup = TestSetup(
        # each container is defined by a dict specifying its networks.
        containers=[
            {"test1": "192.168.0.1", "test2": "192.168.1.1"},
            {"test1": "192.168.2.1", "test2": "192.168.3.1"},
        ],
        ip_addresses=["192.168.4.1", "192.168.5.1", "192.168.0.1", "192.168.1.1"],
    )

    result = test_setup.current_container_finder.current_container()

    assert test_setup.docker_client_mock.mock_calls == [call.containers.list()]
    assert test_setup.ip_retriever_mock.mock_calls == [call.ips()]
    assert (
        result
        == mock_cast(test_setup.docker_client_mock.containers.list).return_value[0]
    )


def test_no_matching_container():
    test_setup = TestSetup(
        containers=[
            {"test1": "192.168.0.1", "test2": "192.168.1.1"},
            {"test1": "192.168.2.1", "test2": "192.168.3.1"},
        ],
        ip_addresses=["192.168.4.1", "192.168.5.1"],
    )

    result = test_setup.current_container_finder.current_container()

    assert test_setup.docker_client_mock.mock_calls == [call.containers.list()]
    assert test_setup.ip_retriever_mock.mock_calls == [call.ips()]
    assert result == None


def test_multiple_containers_matching():
    test_setup = TestSetup(
        containers=[
            {"test1": "192.168.0.1", "test2": "192.168.1.1"},
            {"test1": "192.168.2.1", "test2": "192.168.3.1"},
        ],
        ip_addresses=["192.168.4.1", "192.168.5.1", "192.168.0.1", "192.168.2.1"],
    )

    with pytest.raises(
        RuntimeError, match="Multiple potential current containers found: "
    ):
        test_setup.current_container_finder.current_container()
