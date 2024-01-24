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
from exasol_integration_test_docker_environment.lib.docker.container.utils import \
    remove_docker_container  # type: ignore
from exasol_integration_test_docker_environment.lib.docker.networks.utils import remove_docker_networks  # type: ignore
from exasol_integration_test_docker_environment.lib.docker.volumes.utils import remove_docker_volumes  # type: ignore
from exasol_integration_test_docker_environment.lib.test_environment.docker_container_copy import DockerContainerCopy

from exasol.utils import upward_file_search

TEST_CONTAINER = "itde_manager_test_container"

DB_NETWORK_NAME = "db_network_DemoDb"

DB_VOLUME_NAME = "db_container_DemoDb_volume"

DB_CONTAINER_NAME = "db_container_DemoDb"


def remove_itde():
    remove_docker_container([DB_CONTAINER_NAME])
    remove_docker_networks([DB_NETWORK_NAME])
    remove_docker_volumes([DB_VOLUME_NAME])


@pytest.fixture
def dockerfile() -> str:
    return cleandoc(
        """
        FROM ubuntu:20.04
        
        RUN apt-get update
        RUN apt-get install --yes --no-install-recommends python3 python3-pip git
        RUN python3 -m pip install --upgrade pip 
        """
    )


@pytest.fixture
def docker_image(dockerfile) -> Image:
    with ContextDockerClient() as client:
        image, _ = client.images.build(fileobj=io.BytesIO(dockerfile.encode("UTF-8")))
        yield image
        try:
            client.images.remove(image)
        except Exception as e:
            logging.root.warning("Failed removing image %s with exeception %s", image, e)


@pytest.fixture
def wheel_path() -> Path:
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
        raise RuntimeError(f"Did not find the wheel name in output:\n {output} ")
    return wheel_name


@pytest.fixture
def function_source_code():
    def run_test():
        from exasol.itde_manager import bring_itde_up
        from exasol.secret_store import Secrets
        from pathlib import Path
        from exasol.ai_lab_config import AILabConfig
        from exasol.connections import open_pyexasol_connection

        secrets = Secrets(db_file=Path("secrets.sqlcipher"), master_password="test")
        secrets.save(AILabConfig.mem_size.value, '2')
        secrets.save(AILabConfig.disk_size.value, '4')

        bring_itde_up(secrets)

        con = open_pyexasol_connection(secrets)
        result = con.execute("select 1").fetchmany()
        con.close()
        assert result[0][0] == 1

    function_source_code = textwrap.dedent(dill.source.getsource(run_test))
    source_code = f"{function_source_code}\nrun_test()"
    return source_code


@pytest.fixture
def docker_container(wheel_path, function_source_code, docker_image):
    with ContextDockerClient() as client:
        container = client.containers.run(
            docker_image.id,
            name=TEST_CONTAINER,
            command="sleep infinity",
            detach=True,
            volumes={
                "/var/run/docker.sock": {
                    "bind": "/var/run/docker.sock",
                    "mode": "rw"
                },
            }
        )
        try:
            copy = DockerContainerCopy(container)
            copy.add_file(str(wheel_path), wheel_path.name)
            copy.add_string_to_file("test.py", function_source_code)
            copy.copy("/tmp")
            exit_code, output = container.exec_run(f"python3 -m pip install /tmp/{wheel_path.name} "
                                                   f"--extra-index-url https://download.pytorch.org/whl/cpu")
            assert exit_code == 0, output
            yield container
        finally:
            remove_docker_container([container.id])


def test_bring_itde_up(docker_container):
    exec_result = docker_container.exec_run("python3 /tmp/test.py")
    assert exec_result.exit_code == 0, exec_result.output
