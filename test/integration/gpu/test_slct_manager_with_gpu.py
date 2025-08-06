import textwrap
from collections.abc import (
    Iterator,
)
from pathlib import Path
from tempfile import TemporaryDirectory
from test.integration.ordinary.test_itde_manager import remove_itde

import pytest

from exasol.nb_connector.ai_lab_config import (
    Accelerator,
    AILabConfig,
)
from exasol.nb_connector.itde_manager import bring_itde_up
from exasol.nb_connector.language_container_activation import (
    open_pyexasol_connection_with_lang_definitions,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slct_manager import (
    DEFAULT_SLC_SESSION,
    CondaPackageDefinition,
    SlctManager,
)


@pytest.fixture(scope="session")
def flavor(request) -> str:
    val = "template-Exasol-8-python-3.10-cuda-conda"
    return val


@pytest.fixture(scope="module")
def working_path() -> Iterator[Path]:
    with TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture(scope="module")
def secrets_file(working_path: Path) -> Path:
    return working_path / "sample_database.db"


@pytest.fixture(scope="module")
def slc_secrets(secrets_file, working_path, flavor) -> Secrets:
    secrets = Secrets(secrets_file, master_password="abc")
    secrets.save(
        AILabConfig.slc_target_dir, str(working_path / "script_languages_release")
    )
    DEFAULT_SLC_SESSION.save_flavor(secrets, flavor)
    secrets.save(AILabConfig.accelerator, Accelerator.nvidia.value)
    return secrets


@pytest.fixture(scope="module")
def slct_manager(slc_secrets: Secrets, working_path: Path) -> SlctManager:
    return SlctManager(slc_secrets, working_path)


@pytest.fixture(scope="module")
def itde(slc_secrets: Secrets):
    bring_itde_up(slc_secrets)
    yield
    remove_itde()


@pytest.fixture
def custom_packages() -> list[tuple[str, str, str]]:
    return [("pytorch", "2.7.1=cuda129_generic_py310_h919abc8_203", "pytorch")]


@pytest.mark.dependency(name="clone")
def test_clone_slc(slct_manager):
    slct_manager.clone_slc_repo()


@pytest.mark.dependency(name="test_append_custom_packages", depends=["clone"])
def test_append_custom_packages(
    slct_manager: SlctManager,
    custom_packages: list[tuple[str, str, str]],
):
    slct_manager.append_custom_conda_packages(
        [CondaPackageDefinition(pkg, version) for pkg, version, _ in custom_packages]
    )


@pytest.mark.dependency(
    name="upload_slc_with_new_packages", depends=["test_append_custom_packages"]
)
def test_upload_slc_with_new_packages(
    slc_secrets: Secrets,
    slct_manager: SlctManager,
    custom_packages: list[tuple[str, str, str]],
    flavor,
):
    slct_manager.language_alias = "my_new_python_with_pytorch"
    slct_manager.upload()
    assert (
        slct_manager.activation_key
        == f"my_new_python=localzmq+protobuf:///bfsdefault/default/container/{flavor}-release-my_new_python?lang=python#buckets/bfsdefault/default/container/{flavor}-release-my_new_python/exaudf/exaudfclient"
    )


@pytest.mark.dependency(
    name="udf_with_new_packages", depends=["upload_slc_with_new_packages"]
)
def test_pytorch(
    slc_secrets: Secrets,
    slct_manager: SlctManager,
    custom_packages: list[tuple[str, str, str]],
):
    udf = textwrap.dedent(
        f"""
CREATE OR REPLACE {slct_manager.language_alias} SCALAR SCRIPT
test_gpu_available()
RETURNS VARCHAR(1000) AS
 %perInstanceRequiredAcceleratorDevices GpuNvidia;

import torch

def run(ctx):
    if torch.cuda.is_available():
        return "GPU Found"
    else:
        return "GPU Not Found"
/
        """
    )
    con = open_pyexasol_connection_with_lang_definitions(slc_secrets)
    try:
        con.execute("CREATE SCHEMA TEST")
        con.execute(udf)
        res = con.execute("select test_pytorch()")
        rows = res.fetchall()
        assert rows == [("GPU Found",)]
    finally:
        con.close()
