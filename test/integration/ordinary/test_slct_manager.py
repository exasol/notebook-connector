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
from exasol.nb_connector.slct_manager import (
    PipPackageDefinition,
    SlctManager,
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
    secrets.save(
        AILabConfig.slc_target_dir, str(working_path / "script_languages_release")
    )
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
    return [("xgboost", "2.0.3", "xgboost"), ("scikit-learn", "1.5.0", "sklearn")]


@pytest.mark.dependency(name="clone")
def test_clone_slc(slct_manager):
    slct_manager.clone_slc_repo()


@pytest.mark.dependency(name="check_config", depends=["clone"])
def test_check_slc_config(slct_manager):
    config_ok = slct_manager.check_slc_repo_complete()
    assert config_ok


@pytest.mark.dependency(name="export_slc", depends=["check_config"])
def test_export_slc(slct_manager):
    slct_manager.export()
    export_path = slct_manager.working_path.export_path
    assert export_path.exists()
    tgz = [f for f in export_path.glob("*.tar.gz")]
    assert len(tgz) == 1
    assert tgz[0].is_file()
    tgz_sum = [f for f in export_path.glob("*.tar.gz.sha512sum")]
    assert len(tgz_sum) == 1
    assert tgz_sum[0].is_file()


@pytest.mark.dependency(name="slc_images", depends=["export_slc"])
def test_slc_images(slct_manager):
    images = slct_manager.slc_docker_images
    assert len(images) > 0
    for img in images:
        assert "exasol/script-language-container" in img


@pytest.mark.dependency(name="upload_slc", depends=["check_config"])
def test_upload(slct_manager: SlctManager, itde):
    slct_manager.language_alias = "my_python"
    slct_manager.upload()
    assert (
        slct_manager.activation_key
        == "my_python=localzmq+protobuf:///bfsdefault/default/container/template-Exasol-all-python-3.10-release-my_python?lang=python#buckets/bfsdefault/default/container/template-Exasol-all-python-3.10-release-my_python/exaudf/exaudfclient"
    )


@pytest.mark.dependency(name="append_custom_packages", depends=["upload_slc"])
def test_append_custom_packages(
    slct_manager: SlctManager, custom_packages: list[tuple[str, str, str]]
):
    slct_manager.append_custom_packages(
        [PipPackageDefinition(pkg, version) for pkg, version, _ in custom_packages]
    )
    with open(slct_manager.slc_dir.custom_pip_file) as f:
        pip_content = f.read()
        for custom_package, version, _ in custom_packages:
            assert f"{custom_package}|{version}" in pip_content


@pytest.mark.dependency(
    name="upload_slc_with_new_packages", depends=["append_custom_packages"]
)
def test_upload_slc_with_new_packages(
    slc_secrets: Secrets,
    slct_manager: SlctManager,
    custom_packages: list[tuple[str, str, str]],
):
    slct_manager.language_alias = "my_new_python"
    slct_manager.upload()
    assert (
        slct_manager.activation_key
        == "my_new_python=localzmq+protobuf:///bfsdefault/default/container/template-Exasol-all-python-3.10-release-my_new_python?lang=python#buckets/bfsdefault/default/container/template-Exasol-all-python-3.10-release-my_new_python/exaudf/exaudfclient"
    )


@pytest.mark.dependency(
    name="udf_with_new_packages", depends=["upload_slc_with_new_packages"]
)
def test_udf_with_new_packages(
    slc_secrets: Secrets,
    slct_manager: SlctManager,
    custom_packages: list[tuple[str, str, str]],
):
    import_statements = "\n".join(
        f"    import {module}" for pkg, version, module in custom_packages
    )
    udf = textwrap.dedent(
        f"""
CREATE OR REPLACE {slct_manager.language_alias} SET SCRIPT test_custom_packages(i integer)
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
def test_old_alias(slc_secrets: Secrets, slct_manager: SlctManager):

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
def test_clean_up_images(slct_manager: SlctManager):
    slct_manager.clean_all_images()
    with ContextDockerClient() as docker_client:
        images = docker_client.images.list(name="exasol/script-language-container")
        assert len(images) == 0


@pytest.mark.dependency(name="clean_up_output_path", depends=["clean_up_images"])
def test_clean_output(slct_manager: SlctManager):
    slct_manager.working_path.cleanup_output_path()
    p = Path(slct_manager.working_path.output_path)
    assert not p.is_dir()


@pytest.mark.dependency(name="clean_up_export_path", depends=["clean_up_images"])
def test_clean_export(slct_manager: SlctManager):
    slct_manager.working_path.cleanup_export_path()
    p = Path(slct_manager.working_path.export_path)
    assert not p.is_dir()
