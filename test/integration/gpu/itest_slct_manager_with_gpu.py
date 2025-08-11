import textwrap
from collections.abc import (
    Iterator,
)
from pathlib import Path
from tempfile import TemporaryDirectory

from exasol.nb_connector.slc import ScriptLanguageContainer
from exasol.nb_connector.slc.script_language_container import CondaPackageDefinition
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
def sample_slc(slc_secrets: Secrets, working_path: Path, flavor: str) -> ScriptLanguageContainer:
    return ScriptLanguageContainer.create(slc_secrets, name=name, flavor=flavor)


@pytest.fixture(scope="module")
def slc_secrets(secrets_file, working_path, flavor) -> Secrets:
    secrets = Secrets(secrets_file, master_password="abc")
    secrets.save(AILabConfig.accelerator, Accelerator.nvidia.value)
    return secrets

@pytest.fixture(scope="module")
def sample_slc(slc_secrets: Secrets, working_path: Path, flavor: str) -> ScriptLanguageContainer:
    return ScriptLanguageContainer.create(slc_secrets, name="sample_gpu", flavor=flavor)



@pytest.fixture(scope="module")
def itde(slc_secrets: Secrets):
    bring_itde_up(slc_secrets)
    yield
    remove_itde()


@pytest.fixture
def custom_packages() -> list[tuple[str, str]]:
    return [("numba[cuda]", "0.61.2")]


@pytest.mark.dependency(name="clone")
def test_clone_slc(slct_manager):
    slct_manager.clone_slc_repo()


@pytest.mark.dependency(name="test_append_custom_packages", depends=["clone"])
def test_append_custom_packages(
    sample_slc: ScriptLanguageContainer,
    custom_packages: list[tuple[str, str]],
):
    sample_slc.append_custom_conda_packages(
        [CondaPackageDefinition(pkg, version) for pkg, version in custom_packages]
    )


@pytest.mark.dependency(
    name="upload_slc_with_new_packages", depends=["test_append_custom_packages"]
)
def test_upload_slc_with_new_packages(
    slc_secrets: Secrets,
    itde,
    sample_slc: ScriptLanguageContainer,
    flavor,
):
    sample_slc.deploy()
    assert (
        sample_slc.activation_key
        == f"{sample_slc.language_alias}=localzmq+protobuf:///bfsdefault/default/container/{flavor}-release-{sample_slc.language_alias}?lang=python#buckets/bfsdefault/default/container/{flavor}-release-{sample_slc.language_alias}/exaudf/exaudfclient"
    )


@pytest.mark.dependency(
    name="udf_with_new_packages", depends=["upload_slc_with_new_packages"]
)
def test_numba(
    slc_secrets: Secrets,
    sample_slc: ScriptLanguageContainer,
):
    udf = textwrap.dedent(
        f"""
CREATE OR REPLACE {sample_slc.language_alias} SCALAR SCRIPT
test_gpu_available()
RETURNS VARCHAR(1000) AS
 %perInstanceRequiredAcceleratorDevices GpuNvidia;
from numba import cuda
def run(ctx):
    if cuda.is_available():
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
        res = con.execute("select test_gpu_available()")
        rows = res.fetchall()
        assert rows == [("GPU Found",)]
    finally:
        con.close()