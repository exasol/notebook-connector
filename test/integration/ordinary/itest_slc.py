import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
from test.integration.ordinary.test_itde_manager import remove_itde

import pytest
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

from exasol.nb_connector.itde_manager import bring_itde_up
from exasol.nb_connector.language_container_activation import (
    open_pyexasol_connection_with_lang_definitions,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.script_language_container import (
    PipPackageDefinition,
    ScriptLanguageContainer,
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


def create_slc(
    secrets: Secrets,
    name: str,
    flavor: str = "template-Exasol-all-python-3.10",
) -> ScriptLanguageContainer:
    return ScriptLanguageContainer.create(
        secrets,
        name="MY_SESSION",
        flavor="template-Exasol-all-python-3.10",
    )


@pytest.fixture(scope="module")
def slc_1(slc_secrets: Secrets, working_path: Path) -> ScriptLanguageContainer:
    return create_slc(slc_secrets, "SLC_1")


@pytest.fixture(scope="module")
def slc_2(slc_secrets: Secrets, working_path: Path) -> ScriptLanguageContainer:
    return create_slc(slc_secrets, "SLC_2")


@pytest.fixture
def custom_packages() -> list[tuple[str, str, str]]:
    return [("xgboost", "2.0.3", "xgboost"), ("scikit-learn", "1.5.0", "sklearn")]


@pytest.mark.dependency(name="export_slc")
def test_export_slc(slc_1: ScriptLanguageContainer):
    slc_1.export()
    export_path = slc_1.workspace.export_path
    assert export_path.exists()
    tgz = [f for f in export_path.glob("*.tar.gz")]
    assert len(tgz) == 1
    assert tgz[0].is_file()
    tgz_sum = [f for f in export_path.glob("*.tar.gz.sha512sum")]
    assert len(tgz_sum) == 1
    assert tgz_sum[0].is_file()


@pytest.mark.dependency(name="slc_images", depends=["export_slc"])
def test_slc_images(slc_1: ScriptLanguageContainer):
    images = slc_1.docker_images
    assert len(images) > 0
    for img in images:
        assert "exasol/script-language-container" in img


@pytest.mark.dependency(name="deploy_slc")
def test_deploy(slc_secrets: Secrets, itde):
    # If the intention of this test is to reuse the already created SLC then
    # this test should use the same name "MY_SESSION" rather than creating a
    # new SLC with a different name.
    slc = ScriptLanguageContainer.create(
        slc_secrets,
        name="session_3",
        flavor="template-Exasol-all-python-3.10",
    )
    slc.deploy()
    assert slc.activation_key == (
        "CUSTOM_SLC_SESSION_3=localzmq+protobuf:///bfsdefault/default/container/"
        "template-Exasol-all-python-3.10-release-CUSTOM_SLC_SESSION_3"
        "?lang=python"
        "#buckets/bfsdefault/default/container/"
        "template-Exasol-all-python-3.10-release-CUSTOM_SLC_SESSION_3/"
        "exaudf/exaudfclient"
    )


@pytest.mark.dependency(name="append_custom_packages", depends=["deploy_slc"])
def test_append_custom_packages(
    slc_1: ScriptLanguageContainer, custom_packages: list[tuple[str, str, str]]
):
    # If the intention of this test is to reuse the already created SLC then
    # this test should use the same name "MY_SESSION" rather than creating a
    # new SLC with a different name.
    #
    # Otherwise this tests needs to create a new SLC with a different name And
    # this new SLC needs to be used in dependent test cases such as
    # deploy_slc_with_new_packages.
    slc_1.append_custom_packages(
        [PipPackageDefinition(pkg, version) for pkg, version, _ in custom_packages]
    )
    with open(slc_1.session.custom_pip_file) as f:
        pip_content = f.read()
        for custom_package, version, _ in custom_packages:
            assert f"{custom_package}|{version}" in pip_content


@pytest.mark.dependency(
    name="deploy_slc_with_new_packages", depends=["append_custom_packages"]
)
def test_deploy_slc_with_new_packages(
    slc_secrets: Secrets,
    custom_packages: list[tuple[str, str, str]],
):
    # If the intention of this test is to reuse the already created SLC then
    # this test should use the same name "MY_SESSION" rather than creating a
    # new SLC with a different name.
    slc = ScriptLanguageContainer.create(
        slc_secrets,
        name="session_2",
        flavor="template-Exasol-all-python-3.10",
    )
    slc.deploy()
    assert slc.activation_key == (
        "CUSTOM_SLC_SESSION_2=localzmq+protobuf:///bfsdefault/default/container/"
        "template-Exasol-all-python-3.10-release-CUSTOM_SLC_SESSION_2"
        "?lang=python"
        "#buckets/bfsdefault/default/container/"
        "template-Exasol-all-python-3.10-release-CUSTOM_SLC_SESSION_2/"
        "exaudf/exaudfclient"
    )


@pytest.mark.dependency(
    name="udf_with_new_packages", depends=["deploy_slc_with_new_packages"]
)
def test_udf_with_new_packages(
    slc_secrets: Secrets,
    slc_1: ScriptLanguageContainer,
    custom_packages: list[tuple[str, str, str]],
):
    # If the intention of this test is to reuse the already created SLC then
    # this test should use the same name "MY_SESSION" rather than creating a
    # new SLC with a different name.
    def import_statements(indent: int) -> str:
        separator = "\n" + " " * indent
        return separator.join(
            f"import {module}" for pkg, version, module in custom_packages
        )

    # curently this test fails as the SLC deployed by the test case
    # deploy_slc_with_new_packages above uses a different language alias.
    udf = textwrap.dedent(
        f"""
        CREATE OR REPLACE ALIAS SET SCRIPT test_custom_packages(i integer)
        EMITS (o VARCHAR(2000000)) AS
        def run(ctx):
            {import_statements(indent=12)}

            ctx.emit("success")
        /
        """
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


@pytest.mark.dependency(name="test_old_alias", depends=["udf_with_new_packages"])
def test_old_alias(slc_secrets: Secrets, slc_1: ScriptLanguageContainer):
    # This use case is no longer possible as the alias is generated from the
    # name of an SLC.  So an old alias cannot be reused. Only the complete SLC
    # can be reused. Probably this is the intention of this test case.

    udf = textwrap.dedent(
        f"""
CREATE OR REPLACE my_python SET SCRIPT test_old_slc(i integer)
EMITS (o VARCHAR(2000000)) AS
def run(ctx):
    ctx.emit("success")
/
        """
    )
    con = open_pyexasol_connection_with_lang_definitions(slc_secrets, schema="TEST")
    try:
        con.execute(udf)
        res = con.execute("select test_old_slc(1)")
        rows = res.fetchall()
        assert rows == [("success",)]
    finally:
        con.close()


@pytest.mark.dependency(
    name="clean_up_images", depends=["deploy_slc_with_new_packages"]
)
def test_clean_up_images(slc_1: ScriptLanguageContainer):
    # Cleaning up docker images is specific to each SLC.  Maybe it would make
    # sense to verify that cleaning the docker images of SLC A does not remove
    # the docker images of SLC B.
    slc_1.clean_docker_images()
    with ContextDockerClient() as docker_client:
        images = docker_client.images.list(name="exasol/script-language-container")
        assert len(images) == 0


@pytest.mark.dependency(name="clean_up_output_path", depends=["clean_up_images"])
def test_clean_output(slc_1: ScriptLanguageContainer):
    # Cleaning up directories is specific to the particular SLC.  So the test
    # is expected to remain successful.  Maybe the test could verify that the
    # directories of another SLC remain to exist?
    slc_1.workspace.cleanup_output_path()
    p = Path(slc_1.workspace.output_path)
    assert not p.is_dir()


@pytest.mark.dependency(name="clean_up_export_path", depends=["clean_up_images"])
def test_clean_export(slc_1: ScriptLanguageContainer):
    # Cleaning up directories is specific to the particular SLC.  So the test
    # is expected to remain successful.  Maybe the test could verify that the
    # directories of another SLC remain to exist?
    slc_1.workspace.cleanup_export_path()
    p = Path(slc_1.workspace.export_path)
    assert not p.is_dir()
