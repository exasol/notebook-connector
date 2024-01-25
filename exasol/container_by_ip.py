from typing import (
    Any,
    Dict,
    List,
    Optional,
)

import docker  # type: ignore
import ifaddr
from docker.models.containers import Container  # type: ignore


class IPRetriever:
    def ips(self) -> List[ifaddr.IP]:
        adapters = ifaddr.get_adapters()
        ips = [ip for adapter in adapters for ip in adapter.ips]
        return ips


def retrieve_networks_of_container(
        container: docker.models.containers.Container
) -> List[Dict[str, Any]]:
    container.reload()
    network_settings = container.attrs["NetworkSettings"]
    networks = network_settings["Networks"].values()
    return networks


class ContainerByIp:
    """
    Find a Docker container by ip addresses of its networks
    being included in the given list of ip addresses.
    A single matching ip address is sufficient.
    """

    def __init__(self, docker_client: docker.DockerClient):
        self._docker_client = docker_client

    def find(self, ip_addresses: List[str]) -> Optional[Container]:
        candidates = {
            container
            for container in self._docker_client.containers.list()
            for network in retrieve_networks_of_container(container)
            if network["IPAddress"] in ip_addresses
        }
        if len(candidates) == 1:
            return next(iter(candidates))
        elif len(candidates) == 0:
            return None
        else:
            def format(container):
                return f'{container.id[:12]} "{container.name}"'

            pretty = ", ".join(format(c) for c in candidates)
            raise RuntimeError(f"Multiple potential current containers found: {pretty}")
