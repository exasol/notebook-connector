from typing import Tuple

import docker
from exasol_integration_test_docker_environment.lib import api  # type: ignore
from exasol_integration_test_docker_environment.lib.data.container_info import ContainerInfo
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

from exasol.ai_lab_config import AILabConfig
from exasol.current_container_finder import CurrentContainerFinder
from exasol.secret_store import Secrets

ENVIRONMENT_NAME = "DemoDb"
NAME_SERVER_ADDRESS = "8.8.8.8"


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

    env_info, _ = api.spawn_test_environment(
        environment_name=ENVIRONMENT_NAME,
        nameserver=(NAME_SERVER_ADDRESS,),
        db_mem_size=mem_size,
        db_disk_size=disk_size,
    )

    db_info = env_info.database_info
    container_info = db_info.container_info

    _add_current_container_to_db_network(container_info)

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


def _add_current_container_to_db_network(container_info: ContainerInfo):
    network_name = container_info.network_info.network_name
    docker_client = docker.from_env()
    container = CurrentContainerFinder(docker_client).current_container()
    if container is not None:
        docker_client.networks.get(network_name).connect(container)


def is_itde_running(conf: Secrets) -> Tuple[bool, bool]:
    """
    Checks if the ITDE container exists and if it is running. Returns the two boolean
    flags - (exists, running).
    The name of the container is taken from the provided secret store.
    If the name cannot be found in the secret store the function returns False, False.
    """

    # Try to get the name of the container from the secret store.
    container_name = conf.get(AILabConfig.itde_container)
    if not container_name:
        return False, False

    # Check the existence and the status of the container using the Docker API.
    with ContextDockerClient() as docker_client:
        if docker_client.containers.list(all=True, filters={"name": container_name}):
            container = docker_client.containers.get(container_name)
            return True, container.status == 'running'
        return False, False


def start_itde(conf: Secrets) -> None:
    """
    Starts an existing ITDE container. If the container is already running the function
    takes no effect. For this function to work the container must exist. If it doesn't
    the docker.errors.NotFound exception will be raised. Use the is_itde_running
    function to check if the container exists.

    The name of the container is taken from the provided secret store, where it must
    exist. Otherwise, a RuntimeError will be raised.
    """

    # The name of the container should be in the secret store.
    container_name = conf.get(AILabConfig.itde_container)
    if not container_name:
        raise RuntimeError('Unable to find the name of the Docker container.')

    # Start the container using the Docker API, unless it's already running.
    with ContextDockerClient() as docker_client:
        container = docker_client.containers.get(container_name)
        if container.status != 'running':
            container.start()


def take_itde_down(conf: Secrets) -> None:
    """
    Shuts down the ITDE.
    The names of the docker container, docker volume and docker network
    are taken from the provided secret store. If the names are not found
    there no action is taken.
    """

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
