import textwrap
from collections.abc import Iterator

from test.utils.integration_test_utils import setup_itde_module, sample_db_file

import pytest
from exasol.slc.models.compression_strategy import CompressionStrategy

from exasol.nb_connector.ai_lab_config import (
    Accelerator,
    AILabConfig,
)
from exasol.nb_connector.language_container_activation import (
    open_pyexasol_connection_with_lang_definitions,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc import ScriptLanguageContainer
from exasol.nb_connector.slc.script_language_container import CondaPackageDefinition

DEFAULT_GPU_FLAVOR = "template-Exasol-8-python-3.10-cuda-conda"
"""
The flavor may depend on the release of the SLCR used via SLC_RELEASE_TAG in constants.py.
See the developer guide (./doc/developer-guide.md) for more details.
"""


@pytest.fixture(scope="module")
def secrets_module() -> Iterator[Secrets]:
    with sample_db_file() as secret_db:
        secrets = Secrets(secret_db, master_password="abc")
        secrets.save(AILabConfig.accelerator, Accelerator.nvidia.value)
        yield secrets


@pytest.fixture(scope="module")
def sample_slc(secrets_module: Secrets) -> ScriptLanguageContainer:
    return ScriptLanguageContainer.create(
        secrets_module,
        name="sample_gpu",
        flavor=DEFAULT_GPU_FLAVOR,
        compression_strategy=CompressionStrategy.NONE,
    )


@pytest.fixture
def custom_packages() -> list[tuple[str, str]]:
    return [("numba[cuda]", "0.61.2")]


@pytest.mark.dependency(name="append_custom_packages")
def test_append_custom_packages(
    sample_slc: ScriptLanguageContainer,
    custom_packages: list[tuple[str, str]],
):
    sample_slc.append_custom_conda_packages(
        [CondaPackageDefinition(pkg, version) for pkg, version in custom_packages]
    )


@pytest.mark.dependency(
    name="upload_slc_with_new_packages", depends=["append_custom_packages"]
)
def test_upload_slc_with_new_packages(
    secrets_module: Secrets,
    setup_itde_module,
    sample_slc: ScriptLanguageContainer,
):
    sample_slc.deploy()
    assert (
        sample_slc.activation_key
        == f"{sample_slc.language_alias}=localzmq+protobuf:///bfsdefault/default/container/{DEFAULT_GPU_FLAVOR}-release-{sample_slc.language_alias}?lang=python#buckets/bfsdefault/default/container/{DEFAULT_GPU_FLAVOR}-release-{sample_slc.language_alias}/exaudf/exaudfclient"
    )


@pytest.mark.dependency(
    name="udf_with_new_packages", depends=["upload_slc_with_new_packages"]
)
def test_numba(
    secrets_module: Secrets,
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
    con = open_pyexasol_connection_with_lang_definitions(secrets_module)
    try:
        con.execute("CREATE SCHEMA TEST")
        con.execute(udf)
        res = con.execute("select test_gpu_available()")
        rows = res.fetchall()
        assert rows == [("GPU Found",)]
    finally:
        con.close()
