import json
import os
import shutil
import textwrap
from datetime import (
    timedelta,
)
from pathlib import Path

import docker
import exasol.bucketfs as bfs
import pytest
from exasol.python_extension_common.deployment.extract_validator import ExtractValidator
from exasol.slc.api import push as exaslct_push

from exasol.nb_connector.language_container_activation import (
    open_pyexasol_connection_with_lang_definitions,
)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc import ScriptLanguageContainer
from exasol.nb_connector.slc.constants import PATH_IN_BUCKET
from test.integration.ui.common.utils.notebook_test_utils import run_notebook


def _upload_docker_img_to_cache(slc: ScriptLanguageContainer):
    """
    Building the SLC for the CUDA template flavor takes very long.
    In order to speed up the tests, we upload the container
    """
    if (
        "TARGET_DOCKER_PASSWORD" in os.environ
        and "TARGET_DOCKER_USERNAME" in os.environ
    ):
        target_docker_username = os.environ["TARGET_DOCKER_USERNAME"]
        exaslct_push(
            flavor_path=(str(slc.flavor_path),),
            goal=("release",),
            push_all=True,
            force_push=True,
            target_docker_username=target_docker_username,
        )


def _wait_for_slc_to_become_available(secrets: Secrets, slc: ScriptLanguageContainer):
    def cb(nproc, pending):
        print(f"{len(pending)} of {nproc} nodes are still pending.")

    conn = open_pyexasol_connection_with_lang_definitions(
        secrets, schema=secrets.db_schema, compression=True
    )
    ev = ExtractValidator(
        pyexasol_connection=conn, timeout=timedelta(minutes=5), callback=cb
    )
    url = f"http://{secrets.bfs_host_name}:{secrets.bfs_port}"
    bfs_archive_path = bfs.path.build_path(
        backend=bfs.path.StorageBackend.onprem,
        url=url,
        bucket_name=secrets.bfs_bucket,
        service_name=secrets.bfs_service,
        username="",
        password="",
        verify=False,
        path=f"{PATH_IN_BUCKET}/{slc.flavor}-release-{slc.language_alias}",
    )
    ev.verify_all_nodes(
        schema=secrets.db_schema,
        language_alias=slc.language_alias,
        bfs_archive_path=bfs_archive_path,
    )


def _assert_pytorch_has_single_package_manager(
    secrets: Secrets, slc: ScriptLanguageContainer
) -> None:
    """Ensure PyTorch is not installed through both conda and pip in the SLC."""
    udf = textwrap.dedent(f"""
        CREATE OR REPLACE {slc.language_alias} SCALAR SCRIPT
        check_pytorch_package_provenance()
        RETURNS VARCHAR(2000000) AS
        import json
        import sys
        from importlib.metadata import distributions
        from pathlib import Path

        def normalize_package_name(name):
            return name.lower().replace("-", "").replace("_", "").replace(".", "")

        def conda_pytorch_records():
            records = []
            for record_path in (Path(sys.prefix) / "conda-meta").glob("*.json"):
                with record_path.open(encoding="utf-8") as record_file:
                    record = json.load(record_file)
                if record.get("name") == "pytorch":
                    records.append({{
                        "path": str(record_path),
                        "version": record.get("version"),
                    }})
            return records

        def pip_torch_distributions():
            pip_distributions = []
            for distribution in distributions():
                name = distribution.metadata.get("Name", "")
                if normalize_package_name(name) not in {{"torch", "pytorch"}}:
                    continue
                for distribution_file in distribution.files or []:
                    if distribution_file.name != "INSTALLER":
                        continue
                    installer_path = distribution.locate_file(distribution_file)
                    if installer_path.read_text(encoding="utf-8").strip() == "pip":
                        pip_distributions.append({{
                            "name": name,
                            "version": distribution.version,
                            "path": str(installer_path.parent),
                        }})
            return pip_distributions

        def run(ctx):
            return json.dumps({{
                "conda_pytorch_records": conda_pytorch_records(),
                "pip_torch_distributions": pip_torch_distributions(),
            }})
        /
        """)
    conn = open_pyexasol_connection_with_lang_definitions(
        secrets, schema=secrets.db_schema, compression=True
    )
    try:
        conn.execute(udf)
        rows = conn.execute("SELECT check_pytorch_package_provenance()").fetchall()
    finally:
        conn.close()

    assert len(rows) == 1
    provenance = json.loads(rows[0][0])
    conda_records = provenance["conda_pytorch_records"]
    pip_distributions = provenance["pip_torch_distributions"]
    assert not (conda_records and pip_distributions), (
        "PyTorch is installed through both conda and pip in the GPU SLC: "
        f"conda records={conda_records}, pip distributions={pip_distributions}"
    )


@pytest.fixture()
def check_if_gpu_is_active(request):
    if (value := os.getenv("NBTEST_USE_GPU")) != "true":
        pytest.skip(
            f"Fixture {request.fixturename}(): env NBTEST_USE_GPU = {repr(value)}"
        )


@pytest.fixture()
def docker_login():
    if (
        "TARGET_DOCKER_PASSWORD" in os.environ
        and "TARGET_DOCKER_USERNAME" in os.environ
    ):
        docker_client = docker.from_env(timeout=600)
        docker_client.login(
            username=os.environ["TARGET_DOCKER_USERNAME"],
            password=os.environ["TARGET_DOCKER_PASSWORD"],
        )


@pytest.fixture()
def finish_slc_repo_dir(
    use_saas, backend_setup, check_if_gpu_is_active, notebooks_root
):
    yield
    if not use_saas:
        p = notebooks_root / "gpu_in_udf" / "slc_workspace"
        shutil.rmtree(p)


def test_gpu_notebooks(
    use_saas,
    backend_setup,
    finish_slc_repo_dir,
    uploading_hack,
    docker_login,
    notebooks_root,
) -> None:
    if use_saas:
        pytest.skip(f"use_saas = {use_saas}")
    current_dir = Path.cwd()
    store_path, store_password = backend_setup
    store_file = str(store_path)
    try:
        os.chdir(notebooks_root)
        run_notebook("main_config.ipynb", store_file, store_password)
        os.chdir("./cloud")
        run_notebook("02_s3_vs_reuters.ipynb", store_file, store_password)
        os.chdir("../gpu_in_udf")
        run_notebook("setup.ipynb", store_file, store_password)
        secrets = Secrets(store_path, master_password=store_password)
        slc = ScriptLanguageContainer(secrets=secrets, name="gpu_slc")
        _wait_for_slc_to_become_available(secrets, slc)
        _assert_pytorch_has_single_package_manager(secrets, slc)
        run_notebook("basic_udf_with_gpu.ipynb", store_file, store_password)
        run_notebook(
            "advanced_udf_with_gpu.ipynb",
            store_file,
            store_password,
            hacks=[uploading_hack],
        )
        os.chdir(slc.checkout_dir)
        _upload_docker_img_to_cache(slc)
    finally:
        os.chdir(current_dir)
