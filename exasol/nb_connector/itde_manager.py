from typing import Tuple, Optional
from enum import IntFlag

import docker  # type: ignore
from docker.models.networks import Network # type: ignore
from exasol_integration_test_docker_environment.lib import api  # type: ignore
from exasol_integration_test_docker_environment.lib.data.container_info import ContainerInfo  # type: ignore
from exasol_integration_test_docker_environment.lib.docker import (  # type: ignore
    ContextDockerClient,
)
from exasol_integration_test_docker_environment.lib.docker.container.utils import (  # type: ignore
    remove_docker_container,
)
from exasol_integration_test_docker_environment.lib.docker.networks.utils import (  # type: ignore
    remove_docker_networks,
)
from exasol_integration_test_docker_environment.lib.docker.volumes.utils import (  # type: ignore
    remove_docker_volumes,
)

from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.container_by_ip import ContainerByIp, IPRetriever
from exasol.nb_connector.secret_store import Secrets

ENVIRONMENT_NAME = "DemoDb"
NAME_SERVER_ADDRESS = "8.8.8.8"


class ItdeContainerStatus(IntFlag):
    ABSENT = 0
    STOPPED = 1
    RUNNING = 3
    VISIBLE = 5
    READY = RUNNING | VISIBLE


def bring_itde_up(conf: Secrets) -> None:
    """
    Launches the ITDE environment using its API. Sets hardcoded environment name,
    and Google name server address. Additionally, can set the following
    parameters with values collected from the secret store:
    - database port forwarding,
    - BucketFS port forwarding,
    - database memory size (the value is assumed to be the number of gigabytes),
    - database disk size (the value is assumed to be the number of gigabytes).

    The function assumes that ITDE is not running at the time of the call. If this
    is not the case the behaviour is undefined.

    The names of created docker container, docker volume and docker network will be
    saved in the provided secret store. They will be used by the function that
    takes down the environment.

    The function saves the main AI-Lab configuration parameters, such as the DB and
    BucketFS connection parameters, in the secret store.
    """

    mem_size = f'{conf.get(AILabConfig.mem_size, "4")} GiB'
    disk_size = f'{conf.get(AILabConfig.disk_size, "10")} GiB'

    _remove_current_container_from_db_network(conf)

    env_info, _ = api.spawn_test_environment(
        environment_name=ENVIRONMENT_NAME,
        nameserver=(NAME_SERVER_ADDRESS,),
        db_mem_size=mem_size,
        db_disk_size=disk_size,
    )

    db_info = env_info.database_info
    container_info = db_info.container_info

    _add_current_container_to_db_network(container_info.network_info.network_name)

    conf.save(AILabConfig.itde_container, container_info.container_name)
    conf.save(AILabConfig.itde_volume, container_info.volume_name)
    conf.save(AILabConfig.itde_network, env_info.network_info.network_name)

    conf.save(AILabConfig.db_host_name, db_info.host)
    conf.save(AILabConfig.bfs_host_name, db_info.host)
    conf.save(AILabConfig.db_port, str(db_info.ports.database))
    conf.save(AILabConfig.bfs_port, str(db_info.ports.bucketfs))

    # Q. Can we draw any of the below constants from the ITDE configuration?
    conf.save(AILabConfig.db_user, "sys")
    conf.save(AILabConfig.db_password, "exasol")
    conf.save(AILabConfig.bfs_user, "w")
    conf.save(AILabConfig.bfs_password, "write")
    conf.save(AILabConfig.bfs_service, "bfsdefault")
    conf.save(AILabConfig.bfs_bucket, "default")
    conf.save(AILabConfig.db_encryption, "True")
    # The BucketFS encryption is turned off temporarily.
    conf.save(AILabConfig.bfs_encryption, "False")
    conf.save(AILabConfig.cert_vld, "False")


def _get_current_container(docker_client: docker.DockerClient):
    ip_addresses = _get_ipv4_addresses()
    return ContainerByIp(docker_client).find(ip_addresses)


def _add_current_container_to_db_network(network_name: str) -> None:
    with ContextDockerClient() as docker_client:
        container = _get_current_container(docker_client)
        if not container:
            return
        network = _get_docker_network(docker_client, network_name)
        if network and not _is_container_connected_to_network(container, network):
            network.connect(container.id)


def _is_container_connected_to_network(container, network) -> bool:
    network.reload()
    return container in network.containers


def _is_current_container_visible(network_name: str) -> bool:
    """
    For the Docker Edition returns True if the current (AI-Lab) container
    is connected to the network with the specified name, otherwise False.
    For other editions it always returns True.
    """
    with ContextDockerClient() as docker_client:
        container = _get_current_container(docker_client)
        if not container:
            # Not the Docker Edition
            return True
        network = _get_docker_network(docker_client, network_name)
        if not network:
            return False
        return _is_container_connected_to_network(container, network)


def _get_docker_network(docker_client: docker.DockerClient, network_name: str) -> Optional[Network]:
    networks = docker_client.networks.list(names=[network_name])
    if len(networks) == 1:
        network = networks[0]
        return network
    return None


def _remove_current_container_from_db_network(conf: Secrets):
    network_name = conf.get(AILabConfig.itde_network)
    if not network_name:
        return
    with ContextDockerClient() as docker_client:
        ip_addresses = _get_ipv4_addresses()
        container = ContainerByIp(docker_client).find(ip_addresses)
        if not container:
            return
        network = _get_docker_network(docker_client, network_name)
        if network:
            network.disconnect(container.id)


def _get_ipv4_addresses():
    ip_addresses = [ip.ip for ip in IPRetriever().ips()
                    if ip.is_IPv4 and isinstance(ip.ip, str)]
    return ip_addresses


def get_itde_status(conf: Secrets) -> ItdeContainerStatus:
    """
    Checks if the ITDE container exists and ready to be used. In the Docker Edition that
    means the ITDE is running and the AI-Lab container is connected to its network. In
    other editions it will just check that the ITDE is running.

    Returns the container status.

    The name of the container is taken from the provided secret store.
    If the name cannot be found there the function returns the status ABSENT.
    """

    # Try to get the names of the Docker-DB container and its network from the secret store.
    container_name = conf.get(AILabConfig.itde_container)
    network_name = conf.get(AILabConfig.itde_network)
    if not container_name or not network_name:
        return ItdeContainerStatus.ABSENT

    # Check the existence and the status of the container using the Docker API.
    with ContextDockerClient() as docker_client:
        if docker_client.containers.list(all=True, filters={"name": container_name}):
            container = docker_client.containers.get(container_name)
            if container.status != 'running':
                return ItdeContainerStatus.STOPPED
            status = ItdeContainerStatus.RUNNING
            if _is_current_container_visible(network_name):
                status |= ItdeContainerStatus.VISIBLE
            return status
        return ItdeContainerStatus.ABSENT


def restart_itde(conf: Secrets) -> None:
    """
    Starts an existing ITDE container if it's not already running. In the Docker Edition
    connects the AI-Lab container to the Docker-DB network, unless it's already connected
    to it.

    For this function to work the container must exist. If it doesn't a RuntimeError will
    be raised. Use the get_itde_status function to check if the container exists.
    """

    status = get_itde_status(conf)

    if status is ItdeContainerStatus.ABSENT:
        raise RuntimeError("The Docker-DB container doesn't exist.")

    if ItdeContainerStatus.RUNNING not in status:
        container_name = conf.get(AILabConfig.itde_container)
        with ContextDockerClient() as docker_client:
            container = docker_client.containers.get(container_name)
            container.start()

    if ItdeContainerStatus.VISIBLE not in status:
        network_name = conf.get(AILabConfig.itde_network)
        if network_name:
            _add_current_container_to_db_network(network_name)


def take_itde_down(conf: Secrets) -> None:
    """
    Shuts down the ITDE.
    The names of the docker container, docker volume and docker network
    are taken from the provided secret store. If the names are not found
    there no action is taken.
    """
    _remove_current_container_from_db_network(conf)

    remove_container(conf)
    remove_volume(conf)
    remove_network(conf)

    conf.remove(AILabConfig.db_host_name)
    conf.remove(AILabConfig.bfs_host_name)
    conf.remove(AILabConfig.db_port)
    conf.remove(AILabConfig.bfs_port)
    conf.remove(AILabConfig.db_user)
    conf.remove(AILabConfig.db_password)
    conf.remove(AILabConfig.bfs_user)
    conf.remove(AILabConfig.bfs_password)
    conf.remove(AILabConfig.bfs_service)
    conf.remove(AILabConfig.bfs_bucket)
    conf.remove(AILabConfig.db_encryption)
    conf.remove(AILabConfig.bfs_encryption)
    conf.remove(AILabConfig.cert_vld)


def remove_network(conf):
    network_name = conf.get(AILabConfig.itde_network)
    if network_name:
        remove_docker_networks(iter([network_name]))
        conf.remove(AILabConfig.itde_network)


def remove_volume(conf):
    volume_name = conf.get(AILabConfig.itde_volume)
    if volume_name:
        remove_docker_volumes([volume_name])
        conf.remove(AILabConfig.itde_volume)


def remove_container(conf):
    container_name = conf.get(AILabConfig.itde_container)
    if container_name:
        remove_docker_container([container_name])
        conf.remove(AILabConfig.itde_container)
