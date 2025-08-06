import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
from test.integration.ordinary.test_itde_manager import remove_itde
from typing import (
    List,
    Tuple,
)

import pytest
from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient

from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.itde_manager import bring_itde_up
from exasol.nb_connector.language_container_activation import (
    open_pyexasol_connection_with_lang_definitions,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.constants import PipPackageDefinition
from exasol.nb_connector.slc.script_language_container import (
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
    # secrets.save(
    #     AILabConfig.slc_target_dir, str(working_path / "script_languages_release")
    # )
    # DEFAULT_SLC_SESSION.save_flavor(secrets, "template-Exasol-all-python-3.10")
    return secrets


@pytest.fixture(scope="module")
def sample_slc(slc_secrets: Secrets, working_path: Path) -> ScriptLanguageContainer:
    return ScriptLanguageContainer.create(
        slc_secrets,
        name="my_session",
        flavor="template-Exasol-all-python-3.10",
        language_alias="my_python",
    )


@pytest.fixture(scope="module")
def itde(slc_secrets: Secrets):
    bring_itde_up(slc_secrets)
    yield
    remove_itde()


@pytest.fixture
def custom_packages() -> list[tuple[str, str, str]]:
    return [("xgboost", "2.0.3", "xgboost"), ("scikit-learn", "1.5.0", "sklearn")]


@pytest.mark.dependency(name="clone")
def test_clone_slc(sample_slc: ScriptLanguageContainer):
    sample_slc.clone_slc_repo()


@pytest.mark.dependency(name="check_repo_available", depends=["clone"])
def test_check_slc_config(sample_slc: ScriptLanguageContainer):
    repo_available = sample_slc.slc_repo_available()
    assert repo_available


@pytest.mark.dependency(name="export_slc", depends=["check_repo_available"])
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


@pytest.mark.dependency(name="slc_images", depends=["export_slc"])
def test_slc_images(sample_slc: ScriptLanguageContainer):
    images = sample_slc.slc_docker_images
    assert len(images) > 0
    for img in images:
        assert "exasol/script-language-container" in img


@pytest.mark.dependency(name="upload_slc", depends=["check_repo_available"])
def test_upload(sample_slc: ScriptLanguageContainer, itde):
    sample_slc.language_alias = "my_python"
    sample_slc.upload()
    assert sample_slc.activation_key == (
        "my_python=localzmq+protobuf:///bfsdefault/default/container/"
        "template-Exasol-all-python-3.10-release-my_python"
        "?lang=python"
        "#buckets/bfsdefault/default/container/"
        "template-Exasol-all-python-3.10-release-my_python/"
        "exaudf/exaudfclient"
    )


@pytest.mark.dependency(name="append_custom_packages", depends=["upload_slc"])
def test_append_custom_packages(
    sample_slc: ScriptLanguageContainer, custom_packages: list[tuple[str, str, str]]
):
    sample_slc.append_custom_packages(
        [PipPackageDefinition(pkg, version) for pkg, version, _ in custom_packages]
    )
    # Would we like to move custom_pip_file from SlcSession to ScriptLanguageContainer?
    with open(sample_slc.session.custom_pip_file) as f:
        pip_content = f.read()
        for custom_package, version, _ in custom_packages:
            assert f"{custom_package}|{version}" in pip_content


@pytest.mark.dependency(
    name="upload_slc_with_new_packages", depends=["append_custom_packages"]
)
def test_upload_slc_with_new_packages(
    slc_secrets: Secrets,
    # sample_slc: ScriptLanguageContainer,
    custom_packages: list[tuple[str, str, str]],
):
    slc = ScriptLanguageContainer.create(
        slc_secrets,
        name="session_2",
        flavor="template-Exasol-all-python-3.10",
        language_alias="my_new_python",
    )
    # Do we still need a save method for single attribute, e.g. save
    # language_alias?
    slc.upload()
    assert slc.activation_key == (
        "my_new_python=localzmq+protobuf:///bfsdefault/default/container/"
        "template-Exasol-all-python-3.10-release-my_new_python"
        "?lang=python"
        "#buckets/bfsdefault/default/container/"
        "template-Exasol-all-python-3.10-release-my_new_python/"
        "exaudf/exaudfclient"
    )


@pytest.mark.dependency(
    name="udf_with_new_packages", depends=["upload_slc_with_new_packages"]
)
def test_udf_with_new_packages(
    slc_secrets: Secrets,
    sample_slc: ScriptLanguageContainer,
    custom_packages: list[tuple[str, str, str]],
):
    import_statements = "\n".join(
        f"    import {module}" for pkg, version, module in custom_packages
    )
    udf = textwrap.dedent(
        f"""
CREATE OR REPLACE {sample_slc.language_alias} SET SCRIPT test_custom_packages(i integer)
EMITS (o VARCHAR(2000000)) AS
def run(ctx):
{import_statements}

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
def test_old_alias(slc_secrets: Secrets, sample_slc: ScriptLanguageContainer):

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
    name="clean_up_images", depends=["upload_slc_with_new_packages"]
)
def test_clean_up_images(sample_slc: ScriptLanguageContainer):
    sample_slc.clean_all_images()
    with ContextDockerClient() as docker_client:
        images = docker_client.images.list(name="exasol/script-language-container")
        assert len(images) == 0


@pytest.mark.dependency(name="clean_up_output_path", depends=["clean_up_images"])
def test_clean_output(sample_slc: ScriptLanguageContainer):
    sample_slc.workspace.cleanup_output_path()
    p = Path(sample_slc.workspace.output_path)
    assert not p.is_dir()


@pytest.mark.dependency(name="clean_up_export_path", depends=["clean_up_images"])
def test_clean_export(sample_slc: ScriptLanguageContainer):
    sample_slc.workspace.cleanup_export_path()
    p = Path(sample_slc.workspace.export_path)
    assert not p.is_dir()
