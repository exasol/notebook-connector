import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
from test.integration.ordinary.test_itde_manager import remove_itde

import pytest
from docker.models.images import Image as DockerImage
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

from exasol.nb_connector.itde_manager import bring_itde_up
from exasol.nb_connector.language_container_activation import (
    open_pyexasol_connection_with_lang_definitions,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.script_language_container import (
    PipPackageDefinition,
    ScriptLanguageContainer,
    constants,
)


@pytest.fixture(scope="module")
def working_path() -> Path:
    with TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture(scope="module")
def secrets_file(working_path: Path) -> Path:
    return working_path / "sample_database.db"


@pytest.fixture(scope="module")
def slc_secrets(secrets_file, working_path) -> Secrets:
    secrets = Secrets(secrets_file, master_password="abc")
    return secrets


@pytest.fixture(scope="module")
def itde(slc_secrets: Secrets):
    bring_itde_up(slc_secrets)
    yield
    remove_itde()


DEFAULT_FLAVOR = "template-Exasol-all-python-3.10"
OTHER_FLAVOR = "template-Exasol-all-r-4"
"""
The flavors may depend on the release of the SLCR used via SLC_RELEASE_TAG in constants.py.
See the developer guide (./doc/developer-guide.md) for more details.
"""


def create_slc(
    secrets: Secrets,
    name: str,
    flavor: str = DEFAULT_FLAVOR,
) -> ScriptLanguageContainer:
    return ScriptLanguageContainer.create(secrets, name=name, flavor=flavor)


@pytest.fixture(scope="module")
def sample_slc(slc_secrets: Secrets, working_path: Path) -> ScriptLanguageContainer:
    return create_slc(slc_secrets, "sample")


@pytest.fixture(scope="module")
def other_slc(slc_secrets: Secrets, working_path: Path) -> ScriptLanguageContainer:
    """
    Creates another SLC with a different flavor for verifying operations
    to be limited to the current SLC only, e.g. removing docker images or
    working directories.
    """
    slc = create_slc(slc_secrets, "other", flavor=OTHER_FLAVOR)
    slc.export()
    slc.deploy()
    return slc


@pytest.fixture
def custom_packages() -> list[tuple[str, str, str]]:
    return [("xgboost", "2.0.3", "xgboost"), ("scikit-learn", "1.5.0", "sklearn")]


@pytest.mark.dependency(name="export_slc")
def test_export_slc(sample_slc: ScriptLanguageContainer):
    sample_slc.export()
    export_path = sample_slc.workspace.export_path
    assert export_path.exists()
    tgz = [f for f in export_path.glob("*.tar.gz")]
    assert len(tgz) == 1
    assert tgz[0].is_file()
    tgz_sum = [f for f in export_path.glob("*.tar.gz.sha512sum")]
    assert len(tgz_sum) == 1
    assert tgz_sum[0].is_file()


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
def test_deploy(sample_slc: ScriptLanguageContainer, itde):
    sample_slc.deploy()
    assert sample_slc.activation_key == expected_activation_key(sample_slc)


@pytest.mark.dependency(name="append_custom_packages", depends=["deploy_slc"])
def test_append_custom_packages(
    sample_slc: ScriptLanguageContainer, custom_packages: list[tuple[str, str, str]]
):
    sample_slc.append_custom_packages(
        [PipPackageDefinition(pkg, version) for pkg, version, _ in custom_packages]
    )
    with open(sample_slc.custom_pip_file) as f:
        pip_content = f.read()
        for custom_package, version, _ in custom_packages:
            assert f"{custom_package}|{version}" in pip_content


@pytest.mark.dependency(
    name="deploy_slc_with_custom_packages", depends=["append_custom_packages"]
)
def test_deploy_slc_with_custom_packages(sample_slc: ScriptLanguageContainer):
    sample_slc.deploy()
    assert sample_slc.activation_key == expected_activation_key(sample_slc)


@pytest.mark.dependency(
    name="udf_with_custom_packages",
    depends=["deploy_slc_with_custom_packages"],
)
def test_udf_with_custom_packages(
    slc_secrets: Secrets,
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
    con = open_pyexasol_connection_with_lang_definitions(slc_secrets)
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

    sample_slc.clean_docker_images()
    with ContextDockerClient() as docker_client:
        images = docker_client.images.list(name=constants.SLC_DOCKER_IMG_NAME)

    assert not contains(images, sample_slc)
    assert contains(images, other_slc)


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
