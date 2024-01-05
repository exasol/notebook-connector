from exasol_integration_test_docker_environment.lib import api  # type: ignore
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient  # type: ignore
from exasol_integration_test_docker_environment.lib.docker.container.utils import \
    remove_docker_container  # type: ignore
from exasol_integration_test_docker_environment.lib.docker.networks.utils import remove_docker_networks  # type: ignore
from exasol_integration_test_docker_environment.lib.docker.volumes.utils import remove_docker_volumes  # type: ignore

from exasol.ai_lab_config import AILabConfig
from exasol.secret_store import Secrets

ENVIRONMENT_NAME = "DemoDb"
NAME_SERVER_ADDRESS = "8.8.8.8"

CONTAINER_NAME_KEY = "ITDE_CONTAINER_NAME"
VOLUME_NAME_KEY = "ITDE_VOLUME_NAME"
NETWORK_NAME_KEY = "ITDE_NETWORK_NAME"


def bring_itde_up(conf: Secrets) -> None:
    """
    Launches the ITDE environment using its API. Sets hardcoded environment name,
    and Google name server address. Additionally, can set the following
    parameters with values collected from the secret store:
    - database port forwarding,
    - bucket-fs port forwarding,
    - database memory size (the value is assumed to be the number of gigabytes),
    - database disk size (the value is assumed to be the number of gigabytes).

    The function assumes that ITDE is not running at the time of the call. If this
    is not the case the behaviour is undefined.

    The names of created docker container, docker volume and docker network will be
    saved in the provided secret store. They will be used by the function that
    takes down the environment.

    The function saves the main AI-Lab configuration parameters, such as the DB and
    bucket-fs connection parameters, in the secret store.
    """

    mem_size = f'{conf.get(AILabConfig.mem_size.value)} GiB'
    disk_size = f'{conf.get(AILabConfig.disk_size.value)} GiB'

    env_info, _ = api.spawn_test_environment(
        environment_name=ENVIRONMENT_NAME,
        nameserver=(NAME_SERVER_ADDRESS,),
        db_mem_size=mem_size,
        db_disk_size=disk_size
    )

    db_info = env_info.database_info
    container_info = db_info.container_info

    conf.save(CONTAINER_NAME_KEY, container_info.container_name)
    conf.save(VOLUME_NAME_KEY, container_info.volume_name)
    conf.save(NETWORK_NAME_KEY, env_info.network_info.network_name)

    conf.save(AILabConfig.db_host_name.value, db_info.host)
    conf.save(AILabConfig.bfs_host_name.value, db_info.host)
    conf.save(AILabConfig.db_port.value, str(db_info.ports.database))
    conf.save(AILabConfig.bfs_port.value, str(db_info.ports.bucketfs))

    # Q. Can we draw any of the below constants from the ITDE configuration?
    conf.save(AILabConfig.db_user.value, 'sys')
    conf.save(AILabConfig.db_password.value, 'exasol')
    conf.save(AILabConfig.bfs_user.value, 'w')
    conf.save(AILabConfig.bfs_password.value, 'write')
    conf.save(AILabConfig.bfs_service.value, 'bfsdefault')
    conf.save(AILabConfig.bfs_bucket.value, 'default')
    conf.save(AILabConfig.db_encryption.value, 'True')
    # The bucket-fs encryption is turned off temporarily.
    conf.save(AILabConfig.bfs_encryption.value, 'False')
    conf.save(AILabConfig.cert_vld.value, 'False')


def is_itde_running(conf: Secrets) -> bool:
    """
    Checks if the ITDE container is running.
    The name of the container is taken from the provided secret store.
    If the name cannot be found in the secret store the function returns False.
    """

    container_name = conf.get(CONTAINER_NAME_KEY)
    if not container_name:
        return False

    with ContextDockerClient() as docker_client:
        return bool(docker_client.containers.list(filters={"name": container_name}))


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

    conf.remove(AILabConfig.db_host_name.value)
    conf.remove(AILabConfig.bfs_host_name.value)
    conf.remove(AILabConfig.db_port.value)
    conf.remove(AILabConfig.bfs_port.value)
    conf.remove(AILabConfig.db_user.value)
    conf.remove(AILabConfig.db_password.value)
    conf.remove(AILabConfig.bfs_user.value)
    conf.remove(AILabConfig.bfs_password.value)
    conf.remove(AILabConfig.bfs_service.value)
    conf.remove(AILabConfig.bfs_bucket.value)
    conf.remove(AILabConfig.db_encryption.value)
    conf.remove(AILabConfig.bfs_encryption.value)
    conf.remove(AILabConfig.cert_vld.value)


def remove_network(conf):
    network_name = conf.get(NETWORK_NAME_KEY)
    if network_name:
        remove_docker_networks(iter([network_name]))
        conf.remove(NETWORK_NAME_KEY)


def remove_volume(conf):
    volume_name = conf.get(VOLUME_NAME_KEY)
    if volume_name:
        remove_docker_volumes([volume_name])
        conf.remove(VOLUME_NAME_KEY)


def remove_container(conf):
    container_name = conf.get(CONTAINER_NAME_KEY)
    if container_name:
        remove_docker_container([container_name])
        conf.remove(CONTAINER_NAME_KEY)
