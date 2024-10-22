import io
import logging
import subprocess
import textwrap
from inspect import cleandoc
from pathlib import Path

import dill
import pytest
from docker.models.images import Image
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
from exasol_integration_test_docker_environment.lib.docker.container.utils import (
    remove_docker_container,  # type: ignore
)
from exasol_integration_test_docker_environment.lib.docker.networks.utils import (
    remove_docker_networks,  # type: ignore
)
from exasol_integration_test_docker_environment.lib.docker.volumes.utils import (
    remove_docker_volumes,  # type: ignore
)
from exasol_integration_test_docker_environment.lib.test_environment.docker_container_copy import (
    DockerContainerCopy,
)

from exasol.nb_connector.utils import upward_file_search

# Name of a Docker container used by the tests in this file to manage  ITDE.
TEST_CONTAINER = "itde_manager_container"

DB_NETWORK_NAME = "db_network_DemoDb"

DB_VOLUME_NAME = "db_container_DemoDb_volume"

DB_CONTAINER_NAME = "db_container_DemoDb"


def remove_itde():
    remove_docker_container([DB_CONTAINER_NAME])
    remove_docker_networks([DB_NETWORK_NAME])
    remove_docker_volumes([DB_VOLUME_NAME])


@pytest.fixture
def dockerfile_content() -> str:
    return cleandoc(
        """
        FROM ubuntu:22.04

        RUN apt-get update
        RUN apt-get install --yes --no-install-recommends python3 python3-pip git
        RUN python3 -m pip install --upgrade pip
        """
    )


@pytest.fixture
def docker_image(dockerfile_content) -> Image:
    with ContextDockerClient() as client:
        image, _ = client.images.build(fileobj=io.BytesIO(dockerfile_content.encode("UTF-8")))
        yield image
        try:
            client.images.remove(image)
        except Exception as e:
            logging.root.warning(
                "Failed removing image %s with exception %s", image, e
            )


@pytest.fixture
def wheel_path() -> Path:
    """
    Build the current project (NC) in a subprocess and return the path to the generated wheel file.
    """
    output_bytes = subprocess.check_output(["poetry", "build"])
    wheel_name = find_wheel_name(output_bytes)
    project_root_dir = Path(upward_file_search("pyproject.toml")).parent
    dist_dir = project_root_dir / "dist"
    result = dist_dir / wheel_name
    return result


def find_wheel_name(output_bytes: bytes) -> str:
    output = output_bytes.decode("UTF-8")
    wheel_name = None
    for line in output.splitlines():
        for word in line.split(" "):
            if word.endswith(".whl"):
                wheel_name = word
    if not wheel_name:
        raise RuntimeError(f"Did not find the wheel name in poetry output:\n {output} ")
    return wheel_name


@pytest.fixture
def itde_connect_test_impl():
    """
    This fixture returns the test source code for starting up ITDE and connecting to it.
    The source code needs to appended to the wheel file inside the Docker container called TEST_CONTAINER.
    """

    def run_test():
        from pathlib import Path

        from exasol.nb_connector.ai_lab_config import AILabConfig
        from exasol.nb_connector.connections import open_pyexasol_connection
        from exasol.nb_connector.itde_manager import bring_itde_up
        from exasol.nb_connector.itde_manager import take_itde_down
        from exasol.nb_connector.secret_store import Secrets

        secrets = Secrets(db_file=Path("secrets.sqlcipher"), master_password="test")
        secrets.save(AILabConfig.mem_size.value, "2")
        secrets.save(AILabConfig.disk_size.value, "4")

        bring_itde_up(secrets)
        try:
            con = open_pyexasol_connection(secrets)
            try:
                result = con.execute("select 1").fetchmany()
                assert result[0][0] == 1
            finally:
                con.close()
        finally:
            take_itde_down(secrets)

    function_source_code = textwrap.dedent(dill.source.getsource(run_test))
    source_code = f"{function_source_code}\nrun_test()"
    return source_code


@pytest.fixture
def itde_recreation_after_take_down():
    """
    This fixture returns the test source code for starting up ITDE again, after a first start and take down.
    The source code needs to appended to the wheel file inside the Docker container called TEST_CONTAINER.
    """

    def run_test():
        from pathlib import Path

        from exasol.nb_connector.ai_lab_config import AILabConfig
        from exasol.nb_connector.itde_manager import bring_itde_up
        from exasol.nb_connector.itde_manager import take_itde_down
        from exasol.nb_connector.secret_store import Secrets

        secrets = Secrets(db_file=Path("secrets.sqlcipher"), master_password="test")
        secrets.save(AILabConfig.mem_size.value, "2")
        secrets.save(AILabConfig.disk_size.value, "4")

        bring_itde_up(secrets)
        take_itde_down(secrets)
        bring_itde_up(secrets)
        take_itde_down(secrets)

    function_source_code = textwrap.dedent(dill.source.getsource(run_test))
    source_code = f"{function_source_code}\nrun_test()"
    return source_code


@pytest.fixture
def itde_recreation_without_take_down():
    """
    This fixture returns the test source code for starting up ITDE again, after a first start and no take down.
    The source code needs to appended to the wheel file inside the Docker container called TEST_CONTAINER.
    """

    def run_test():
        from pathlib import Path

        from exasol.nb_connector.ai_lab_config import AILabConfig
        from exasol.nb_connector.itde_manager import bring_itde_up
        from exasol.nb_connector.itde_manager import take_itde_down
        from exasol.nb_connector.secret_store import Secrets

        secrets = Secrets(db_file=Path("secrets.sqlcipher"), master_password="test")
        secrets.save(AILabConfig.mem_size.value, "2")
        secrets.save(AILabConfig.disk_size.value, "4")

        bring_itde_up(secrets)
        bring_itde_up(secrets)
        take_itde_down(secrets)

    function_source_code = textwrap.dedent(dill.source.getsource(run_test))
    source_code = f"{function_source_code}\nrun_test()"
    return source_code


@pytest.fixture
def itde_stop_and_restart():
    """
    This fixture returns the test source code for restarting ITDE after its container is stopped
    and the calling container is disconnected from its network.
    The source code needs to appended to the wheel file inside the Docker container called TEST_CONTAINER.
    """

    def run_test():
        from pathlib import Path

        from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient
        from exasol.nb_connector.ai_lab_config import AILabConfig
        from exasol.nb_connector.itde_manager import (
            ItdeContainerStatus, bring_itde_up, restart_itde, get_itde_status,
            _remove_current_container_from_db_network)
        from exasol.nb_connector.secret_store import Secrets

        secrets = Secrets(db_file=Path("secrets.sqlcipher"), master_password="test")
        secrets.save(AILabConfig.mem_size.value, "2")
        secrets.save(AILabConfig.disk_size.value, "4")

        bring_itde_up(secrets)
        status = get_itde_status(secrets)
        assert status is ItdeContainerStatus.READY, f'The status after bringing itde up is {status.name}'

        # Disconnect calling container from Docker-DB network
        _remove_current_container_from_db_network(secrets)
        status = get_itde_status(secrets)
        assert status is ItdeContainerStatus.RUNNING, f'The status after disconnecting the container is {status.name}'

        # Stop the Docker-DB container.
        container_name = secrets.get(AILabConfig.itde_container)
        with ContextDockerClient() as docker_client:
            docker_client.api.stop(container_name)
        status = get_itde_status(secrets)
        assert status is ItdeContainerStatus.STOPPED, f'The status after stopping ITDE is {status.name}'

        restart_itde(secrets)
        status = get_itde_status(secrets)
        assert status is ItdeContainerStatus.RUNNING, f'The status after restarting ITDE is {status.name}'

    function_source_code = textwrap.dedent(dill.source.getsource(run_test))
    source_code = f"{function_source_code}\nrun_test()"
    return source_code


@pytest.fixture
def itde_external_test():
    """
    This fixture returns the test source code for testing the use of an externally created ITDE.
    The source code needs to appended to the wheel file inside the Docker container called TEST_CONTAINER.
    """

    def run_test():
        from pathlib import Path
        from unittest.mock import patch

        from exasol_integration_test_docker_environment.lib import api
        from exasol.nb_connector.connections import open_pyexasol_connection
        from exasol.nb_connector.itde_manager import bring_itde_up, take_itde_down
        from exasol.nb_connector.secret_store import Secrets

        secrets = Secrets(db_file=Path("secrets.sqlcipher"), master_password="test")
        env_info, cleanup_func = api.spawn_test_environment(environment_name="TestDemoDb")
        try:
            with patch('exasol_integration_test_docker_environment.lib.api.spawn_test_environment'):
                # We have effectively disabled the spawn_test_environment(). The bring_itde_up()
                # should use the provided instance of the DockerDB. If it tries to create a new
                # one this will fail since a spawn_test_environment() mock will be called instead.
                # The mock will not return a valid EnvironmentInfo object.
                bring_itde_up(secrets, env_info)
                with open_pyexasol_connection(secrets) as conn:
                    result = conn.execute("select 1").fetchval()
                    assert result == 1
                take_itde_down(secrets, False)
        finally:
            cleanup_func()

    function_source_code = textwrap.dedent(dill.source.getsource(run_test))
    source_code = f"{function_source_code}\nrun_test()"
    return source_code


@pytest.fixture
def docker_container(wheel_path, docker_image,
                     itde_connect_test_impl,
                     itde_recreation_after_take_down,
                     itde_recreation_without_take_down,
                     itde_stop_and_restart,
                     itde_external_test):
    """
    Create a Docker container named TEST_CONTAINER to manage an instance of ITDE.
    Copy the wheel file resulting from building the current project NC into the container.
    Append a script to the wheel file inside the container and execute it.
    The script then will bring up the ITDE, running in yet another Docker container.
    """
    with ContextDockerClient() as client:
        container = client.containers.run(
            docker_image.id,
            name=TEST_CONTAINER,
            command="sleep infinity",
            detach=True,
            volumes={
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"},
            },
        )
        try:
            copy = DockerContainerCopy(container)
            copy.add_file(str(wheel_path), wheel_path.name)
            copy.add_string_to_file("itde_connect_test_impl.py", itde_connect_test_impl)
            copy.add_string_to_file("itde_recreation_after_take_down.py", itde_recreation_after_take_down)
            copy.add_string_to_file("itde_recreation_without_take_down.py", itde_recreation_without_take_down)
            copy.add_string_to_file("itde_stop_and_restart.py", itde_stop_and_restart)
            copy.add_string_to_file("itde_external_test.py", itde_external_test)
            copy.copy("/tmp")
            exit_code, output = container.exec_run(
                f"python3 -m pip install /tmp/{wheel_path.name} "
                f"--extra-index-url https://download.pytorch.org/whl/cpu"
            )
            assert exit_code == 0, output
            yield container
        finally:
            remove_docker_container([container.id])


def test_itde_connect(docker_container):
    exec_result = docker_container.exec_run("python3 /tmp/itde_connect_test_impl.py")
    assert exec_result.exit_code == 0, exec_result.output


def test_itde_recreation_after_take_down(docker_container):
    exec_result = docker_container.exec_run("python3 /tmp/itde_recreation_after_take_down.py")
    assert exec_result.exit_code == 0, exec_result.output


def test_itde_recreation_without_take_down(docker_container):
    exec_result = docker_container.exec_run("python3 /tmp/itde_recreation_without_take_down.py")
    assert exec_result.exit_code == 0, exec_result.output


_IGNORE_WARNINGS1 = (
    '-W "ignore::DeprecationWarning:luigi.*:" '
    '-W "ignore::DeprecationWarning:pkg_resources.*:" '
    '-W "ignore:pkg_resources is deprecated as an API:DeprecationWarning" '
    '-W "ignore::DeprecationWarning:exasol_integration_test_docker_environment.*:"'
)


_IGNORE_WARNINGS = " ".join(
    f'-W "ignore:{w}"' for w in [
        ":DeprecationWarning:luigi.*:",
        ":DeprecationWarning:pkg_resources.*:",
        "pkg_resources is deprecated as an API:DeprecationWarning",
        ":DeprecationWarning:exasol_integration_test_docker_environment.*:",
        ])


def test_x1():
    print(f'{_IGNORE_WARNINGS}')
    assert _IGNORE_WARNINGS == _IGNORE_WARNINGS1

def test_itde_stop_and_restart(docker_container):
    exec_result = docker_container.exec_run(f"python3 {_IGNORE_WARNINGS} /tmp/itde_stop_and_restart.py")
    assert exec_result.exit_code == 0, exec_result.output


def test_itde_external(docker_container):
    exec_result = docker_container.exec_run("python3 /tmp/itde_external_test.py")
    assert exec_result.exit_code == 0, exec_result.output
