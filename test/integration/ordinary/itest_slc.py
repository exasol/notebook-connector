import os
import textwrap
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from test.package_manager import PackageManager
from test.utils.integration_test_utils import setup_itde_module

import pytest
from docker.models.images import Image as DockerImage
from exasol.slc.models.compression_strategy import CompressionStrategy
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

from exasol.nb_connector.language_container_activation import (
    open_pyexasol_connection_with_lang_definitions,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.script_language_container import (
    CondaPackageDefinition,
    PipPackageDefinition,
    ScriptLanguageContainer,
    constants,
)

DEFAULT_FLAVORS = {
    PackageManager.PIP: "template-Exasol-all-python-3.10",
    PackageManager.CONDA: "template-Exasol-all-python-3.10-conda",
}

OTHER_FLAVOR = "template-Exasol-all-r-4"
"""
The flavors may depend on the release of the SLCR used via SLC_RELEASE_TAG in constants.py.
See the developer guide (./doc/developer-guide.md) for more details.
"""


@pytest.fixture(scope="module")
def temp_cwd() -> Iterator[Path]:
    old_cwd = Path.cwd()
    with TemporaryDirectory() as tmpdir:
        new_cwd = Path(tmpdir)
        os.chdir(new_cwd)
        yield new_cwd
    os.chdir(old_cwd)


@pytest.fixture(scope="module")
def default_flavor(package_manager: PackageManager) -> str:
    return DEFAULT_FLAVORS[package_manager]


def create_slc(
    secrets: Secrets,
    name: str,
    flavor: str,
    compression_strategy: CompressionStrategy,
) -> ScriptLanguageContainer:
    return ScriptLanguageContainer.create(
        secrets, name=name, flavor=flavor, compression_strategy=compression_strategy
    )


@pytest.fixture(scope="module")
def sample_slc(
    temp_cwd: Path,
    secrets_module: Secrets,
    default_flavor: str,
    compression_strategy: CompressionStrategy,
) -> ScriptLanguageContainer:
    return create_slc(secrets_module, "sample", default_flavor, compression_strategy)


@pytest.fixture(scope="module")
def other_slc(
    temp_cwd: Path, secrets_module: Secrets, compression_strategy: CompressionStrategy
) -> ScriptLanguageContainer:
    """
    Creates another SLC with a different flavor for verifying operations
    to be limited to the current SLC only, e.g. removing docker images or
    working directories.
    """
    slc = create_slc(
        secrets_module,
        "other",
        flavor=OTHER_FLAVOR,
        compression_strategy=compression_strategy,
    )
    slc.export()
    slc.deploy()
    return slc


@pytest.fixture
def custom_packages() -> list[tuple[str, str, str]]:
    return [("xgboost", "2.0.3", "xgboost"), ("scikit-learn", "1.5.0", "sklearn")]


def _check_exported_slc_exists(expected_suffix: str, expected_path: Path) -> None:
    tar = [f for f in expected_path.glob(f"*.{expected_suffix}")]
    assert len(tar) == 1
    assert tar[0].is_file()
    tar_sum = [f for f in expected_path.glob(f"*.{expected_suffix}.sha512sum")]
    assert len(tar_sum) == 1
    assert tar_sum[0].is_file()


@pytest.mark.dependency(name="export_slc_no_copy")
def test_export_slc_no_copy(
    sample_slc: ScriptLanguageContainer, compression_strategy: CompressionStrategy
):
    sample_slc.export_no_copy()
    export_path = sample_slc.workspace.export_path
    expected_suffix = (
        "tar" if compression_strategy == CompressionStrategy.NONE else "tar.gz"
    )
    assert not export_path.exists()

    internal_export_path = sample_slc.workspace.output_path / "cache" / "exports"
    _check_exported_slc_exists(expected_suffix, internal_export_path)


@pytest.mark.dependency(name="export_slc", depends=["export_slc_no_copy"])
def test_export_slc(
    sample_slc: ScriptLanguageContainer, compression_strategy: CompressionStrategy
):
    sample_slc.export()
    export_path = sample_slc.workspace.export_path
    expected_suffix = (
        "tar" if compression_strategy == CompressionStrategy.NONE else "tar.gz"
    )
    assert export_path.exists()
    _check_exported_slc_exists(expected_suffix, export_path)


def slc_docker_tag_prefix(slc: ScriptLanguageContainer) -> str:
    return f"{constants.SLC_DOCKER_IMG_NAME}:{slc.flavor}"


@pytest.mark.dependency(name="slc_images", depends=["export_slc"])
def test_slc_images(sample_slc: ScriptLanguageContainer):
    images = sample_slc.docker_image_tags
    assert len(images) > 0
    expected = slc_docker_tag_prefix(sample_slc)
    for img in images:
        assert expected in img


def expected_activation_key(slc: ScriptLanguageContainer) -> str:
    alias = slc.language_alias
    bfs_path = f"default/container/{slc.flavor}-release-{alias}"
    return (
        f"{alias}=localzmq+protobuf:///bfsdefault/{bfs_path}?lang=python"
        f"#buckets/bfsdefault/{bfs_path}/exaudf/exaudfclient"
    )


@pytest.mark.dependency(name="deploy_slc")
def test_deploy(sample_slc: ScriptLanguageContainer, setup_itde_module):
    sample_slc.deploy()
    assert sample_slc.activation_key == expected_activation_key(sample_slc)


@pytest.mark.dependency(name="append_custom_pip_packages", depends=["deploy_slc"])
def test_append_custom_pip_packages(
    sample_slc: ScriptLanguageContainer,
    custom_packages: list[tuple[str, str, str]],
    package_manager: PackageManager,
):
    # Cannot skip the test if it's not a Pip package manager, otherwise dependent tests below won't run
    if package_manager == PackageManager.PIP:
        sample_slc.append_custom_pip_packages(
            [PipPackageDefinition(pkg, version) for pkg, version, _ in custom_packages]
        )
        with open(sample_slc.custom_pip_file) as f:
            pip_content = f.read()
            for custom_package, version, _ in custom_packages:
                assert f"{custom_package}|{version}" in pip_content


@pytest.mark.dependency(name="append_custom_conda_packages", depends=["deploy_slc"])
def test_append_custom_conda_packages(
    sample_slc: ScriptLanguageContainer,
    custom_packages: list[tuple[str, str, str]],
    package_manager: PackageManager,
):
    # Cannot skip the test if it's not a Conda package manager, otherwise dependent tests below won't run
    if package_manager == PackageManager.CONDA:
        sample_slc.append_custom_conda_packages(
            [
                CondaPackageDefinition(pkg, version)
                for pkg, version, _ in custom_packages
            ]
        )
        with open(sample_slc.custom_conda_file) as f:
            conda_content = f.read()
            for custom_package, version, _ in custom_packages:
                assert f"{custom_package}|{version}" in conda_content


@pytest.mark.dependency(
    name="deploy_slc_with_custom_packages",
    depends=["append_custom_pip_packages", "append_custom_conda_packages"],
)
def test_deploy_slc_with_custom_packages(
    sample_slc: ScriptLanguageContainer, setup_itde_module
):
    sample_slc.deploy()
    assert sample_slc.activation_key == expected_activation_key(sample_slc)


@pytest.mark.dependency(
    name="udf_with_custom_packages",
    depends=["deploy_slc_with_custom_packages"],
)
def test_udf_with_custom_packages(
    secrets_module: Secrets,
    sample_slc: ScriptLanguageContainer,
    custom_packages: list[tuple[str, str, str]],
):
    import_statements = "\n    ".join(
        f"import {module}" for pkg, version, module in custom_packages
    )
    udf = textwrap.dedent(
        """
        CREATE OR REPLACE {language_alias}
        SET SCRIPT test_custom_packages(i integer)
        EMITS (o VARCHAR(2000000)) AS
        def run(ctx):
            {import_statements}

            ctx.emit("success")
        /
        """
    ).format(
        language_alias=sample_slc.language_alias,
        import_statements=import_statements,
    )
    con = open_pyexasol_connection_with_lang_definitions(secrets_module)
    try:
        con.execute("CREATE SCHEMA TEST")
        con.execute(udf)
        res = con.execute("select test_custom_packages(1)")
        rows = res.fetchall()
        assert rows == [("success",)]
    finally:
        con.close()


@pytest.mark.dependency(
    name="clean_docker_images", depends=["deploy_slc_with_custom_packages"]
)
def test_clean_docker_images(
    sample_slc: ScriptLanguageContainer,
    other_slc: ScriptLanguageContainer,
):
    def contains(
        images: list[DockerImage],
        slc: ScriptLanguageContainer,
    ) -> list[str]:
        prefix = slc_docker_tag_prefix(slc)
        return [tag for img in images if (tag := img.tags[0]).startswith(prefix)]

    output_path = Path.cwd() / "clean_docker_images_output"

    ScriptLanguageContainer.clean_docker_images(output_path=output_path)
    with ContextDockerClient() as docker_client:
        images = docker_client.images.list(name=constants.SLC_DOCKER_IMG_NAME)

    assert not contains(images, sample_slc)
    assert not contains(images, other_slc)
    assert len(list(output_path.iterdir())) > 0


@pytest.mark.dependency(name="clean_up_output_path", depends=["clean_docker_images"])
def test_clean_output(
    sample_slc: ScriptLanguageContainer,
    other_slc: ScriptLanguageContainer,
):
    def output_path_exists(slc: ScriptLanguageContainer) -> bool:
        return slc.workspace.output_path.is_dir()

    sample_slc.workspace.cleanup_output_path()
    assert not output_path_exists(sample_slc)
    assert output_path_exists(other_slc)


@pytest.mark.dependency(name="clean_up_export_path", depends=["clean_docker_images"])
def test_clean_export(
    sample_slc: ScriptLanguageContainer,
    other_slc: ScriptLanguageContainer,
):
    def export_path_exists(slc: ScriptLanguageContainer) -> bool:
        return slc.workspace.export_path.is_dir()

    sample_slc.workspace.cleanup_export_path()
    assert not export_path_exists(sample_slc)
    assert export_path_exists(other_slc)
