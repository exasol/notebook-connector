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

from exasol.utils import upward_file_search

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
        FROM ubuntu:20.04
        
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
def itde_startup_impl():
    """
    This fixture returns the source code for starting up ITDE.
    The source code needs to appended to the wheel file inside the Docker container called TEST_CONTAINER.
    """

    def run_test():
        from pathlib import Path

        from exasol.ai_lab_config import AILabConfig
        from exasol.connections import open_pyexasol_connection
        from exasol.itde_manager import bring_itde_up
        from exasol.itde_manager import take_itde_down
        from exasol.secret_store import Secrets

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
def docker_container(wheel_path, itde_startup_impl, docker_image):
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
            copy.add_string_to_file("test.py", function_source_code)
            copy.copy("/tmp")
            exit_code, output = container.exec_run(
                f"python3 -m pip install /tmp/{wheel_path.name} "
                f"--extra-index-url https://download.pytorch.org/whl/cpu"
            )
            assert exit_code == 0, output
            yield container
        finally:
            remove_docker_container([container.id])


def test_bring_itde_up(docker_container):
    exec_result = docker_container.exec_run("python3 /tmp/test.py")
    assert exec_result.exit_code == 0, exec_result.output
