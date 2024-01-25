from typing import (
    Any,
    Dict,
    List,
    Optional,
)

import docker # type: ignore
import ifaddr
from docker.models.containers import Container # type: ignore


class IPRetriever:
    def ips(self) -> List[ifaddr.IP]:
        adapters = ifaddr.get_adapters()
        ips = [ip for adapter in adapters for ip in adapter.ips]
        return ips


class CurrentContainerFinder:
    def __init__(
        self,
        docker_client: docker.DockerClient,
        ip_retriever: IPRetriever = IPRetriever(),
    ):
        self._ip_retriever = ip_retriever
        self._docker_client = docker_client

    def current_container(self) -> Optional[Container]:
        ips = self._ip_retriever.ips()
        ip_addresses = {ip.ip for ip in ips}
        candidates = {
            container
            for container in self._docker_client.containers.list()
            for network in self.retrieve_networks_of_container(container)
            if network["IPAddress"] in ip_addresses
        }
        if len(candidates) == 1:
            return next(iter(candidates))
        elif len(candidates) == 0:
            return None
        else:
            raise RuntimeError(
                f"Multiple potential current containers found: {candidates}"
            )

    def retrieve_networks_of_container(
        self, container: docker.models.containers.Container
    ) -> List[Dict[str, Any]]:
        container.reload()
        network_settings = container.attrs["NetworkSettings"]
        networks = network_settings["Networks"].values()
        return networks
