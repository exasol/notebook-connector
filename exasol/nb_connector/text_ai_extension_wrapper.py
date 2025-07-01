import subprocess
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from os import PathLike
from pathlib import Path
from typing import (
    Optional,
)

import requests

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.extension_wrapper_common import (
    deploy_language_container,
    encapsulate_bucketfs_credentials,
)
from exasol.nb_connector.language_container_activation import ACTIVATION_KEY_PREFIX
from exasol.nb_connector.secret_store import Secrets

# Models will be uploaded into directory BFS_MODELS_DIR in BucketFS.
#
# Models downloaded from the Huggingface archive to a local drive will be
# cached in directory MODELS_CACHE_DIR.
#
# TXAIE uses the same directories as TE (see function initialize_te_extension)
# as both extensions are using Huggingface Models. This also avoids confusion,
# and ensures backwards compatibility.
from exasol.nb_connector.transformers_extension_wrapper import (
    BFS_MODELS_DIR,
    MODELS_CACHE_DIR,
)

PATH_IN_BUCKET = "TXAIE"
""" Location in BucketFS bucket to upload data for TXAIE, e.g. its language container. """

LANGUAGE_ALIAS = "PYTHON3_TXAIE"

LATEST_KNOWN_VERSION = "???"

ACTIVATION_KEY = ACTIVATION_KEY_PREFIX + "txaie"
"""
Activation SQL for the Text AI Extension will be saved in the secret store
with this key.

TXAIE brings its own Script Language Container (SLC) which needs to be
activated by a dedicated SQL statement `ALTER SESSION SET SCRIPT_LANGUAGES`.  Applications
can store the language definition in the configuration store (SCS) from the Notebook
Connector's class `exasol.nb_connector.secret_store.Secrets`.

Using `ACTIVATION_KEY` as defined key, TXAIE can provide convenient interfaces
accepting only the SCS and retrieving all further data from the there.
"""

BFS_CONNECTION_PREFIX = "TXAIE_BFS"
"""
Prefix for Exasol CONNECTION objects containing a BucketFS location and
credentials.
"""


@contextmanager
def download_pre_release(conf: Secrets) -> Generator[tuple[Path, Path], None, None]:
    """
    Downloads and unzips the pre-release archive. Returns the paths to the temporary
    files of the project wheel and the SLC.

    Usage:
    with download_pre_release(conf) as unzipped_files:
        project_wheel, slc_tar_gz = unzipped_files
        ...
    """

    zip_url = conf.get(CKey.text_ai_pre_release_url)
    if not zip_url:
        raise ValueError("Pre-release URL is not set.")
    zip_password = conf.get(CKey.text_ai_zip_password)
    if not zip_password:
        raise ValueError("Pre-release zip password is not set.")

    # Download the file
    response = requests.get(zip_url, stream=True)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile() as tmp_file:
        # Save the downloaded zip in a temporary file
        for chunk in response.iter_content(chunk_size=1048576):
            tmp_file.write(chunk)
        tmp_file.flush()
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Unzip the file into a temporary directory
            unzip_cmd = [
                "unzip",
                "-q",
                "-P",
                zip_password,
                tmp_file.name,
                "-d",
                tmp_dir,
            ]
            subprocess.run(unzip_cmd, check=True, capture_output=True)
            tmp_path = Path(tmp_dir)
            # Find and return the project wheel and the SLC
            project_wheel = next(tmp_path.glob("*.whl"))
            slc_tar_gz = next(tmp_path.glob("*.tar.gz"))
            conf.save(CKey.txaie_slc_file_local_path, str(slc_tar_gz))
            yield project_wheel, slc_tar_gz


def deploy_licence(
    conf: Secrets,
    licence_file: Optional[Path] = None,
    licence_content: Optional[str] = None,
) -> None:
    """
    Deploys the given license and saves its identifier to the secret store. The licence can either be
    defined by a path pointing to a licence file, or by the licence content given as a string.
    Parameters:
         conf:
            The secret store.
        licence_file:
            Optional. Path of a licence file.
        licence_content:
            Optional. Content of a licence given as a string.

    """
    raise NotImplementedError(
        "Currently this is not implemented, "
        "will be changed once the licensing process is finalized."
    )


def initialize_text_ai_extension(
    conf: Secrets,
    container_file: Optional[Path] = None,
    version: Optional[str] = None,
    language_alias: str = LANGUAGE_ALIAS,
    run_deploy_container: bool = True,
    run_deploy_scripts: bool = False,
    run_upload_models: bool = False,
    run_encapsulate_bfs_credentials: bool = True,
    allow_override: bool = True,
) -> None:
    """
    Depending on which flags are set, runs different steps to install Text-AI Extension in the DB.
    Possible steps:

    * Call the Text-AI Extension's language container deployment API.
    If given a version, downloads the specified released version of the extension from ???
    and uploads it to the BucketFS.

    If given a container_file path instead, installs the given container in the Bucketfs.

    If neither is given, checks if txaie_slc_file_local_path is set and installs this SLC if found,
    otherwise attempts to install the latest version from t.b.d.

    This function doesn't activate the language container. Instead, it gets the
    activation SQL using the same API and writes it to the secret store. The name
    of the key is defined in the ACTIVATION_KEY constant.

    * Install default transformers models into
    the Bucketfs using Transformers Extensions upload model functionality.

    * Install Text-AI specific scripts.

    Parameters:
        conf:
            The secret store. The store must contain the DB connection parameters
            and the parameters of the BucketFS service.
        container_file:
            Optional. Path pointing to the locally stored Script Language Container file for the Text-AI Extension.
        version:
            Optional. Text-AI extension version.
        language_alias:
            The language alias of the extension's language container.
        run_deploy_container:
            If True runs deployment of the locally stored Script Language Container file for the Text-AI Extension.
        run_deploy_scripts:
            If True runs deployment of Text-AI Extension scripts.
        run_upload_models:
            If True uploads default Transformers models to the BucketFS.
        run_encapsulate_bfs_credentials:
            If set to False will skip the creation of the text ai specific database connection
            object encapsulating the BucketFS credentials.
        allow_override:
            If True allows overriding the language definition.
    """

    # Create the name of the Exasol connection object
    db_user = str(conf.get(CKey.db_user))
    bfs_conn_name = "_".join([BFS_CONNECTION_PREFIX, db_user])
    # As soon as the official release of TXAIE is available, the hard-coded value for
    # container_name can be replaced by TXAIELanguageContainerDeployer.SLC_NAME,
    # see https://github.com/exasol/notebook-connector/issues/179.
    container_name = "exasol_text_ai_extension_container_release.tar.gz"

    def from_ai_lab_config(key: CKey) -> Path | None:
        entry = conf.get(key)
        return Path(entry) if entry else None

    if run_deploy_container:
        if version:
            install_text_ai_extension(version)
            # Can run_upload_models, run_deploy_scripts,
            # run_encapsulate_bfs_credentials, etc. be ignored here?
            return

        container_file = container_file or from_ai_lab_config(
            CKey.txaie_slc_file_local_path
        )
        if not container_file:
            install_text_ai_extension(LATEST_KNOWN_VERSION)
        else:
            deploy_language_container(
                conf=conf,
                path_in_bucket=PATH_IN_BUCKET,
                language_alias=language_alias,
                activation_key=ACTIVATION_KEY,
                container_file=container_file,
                container_name=container_name,
                allow_override=allow_override,
            )

    if run_upload_models:
        #  Install default Hugging Face models into the Bucketfs using
        #  Transformers Extensions upload model functionality.
        raise NotImplementedError("Implementation is waiting for TE release.")

    if run_deploy_scripts:
        raise NotImplementedError(
            "Currently there are no Text-AI specific scripts to deploy."
        )

    if run_encapsulate_bfs_credentials:
        encapsulate_bucketfs_credentials(
            conf, path_in_bucket=PATH_IN_BUCKET, connection_name=bfs_conn_name
        )

    # Update secret store
    conf.save(CKey.txaie_bfs_connection, bfs_conn_name)
    conf.save(CKey.txaie_models_bfs_dir, BFS_MODELS_DIR)
    conf.save(CKey.txaie_models_cache_dir, MODELS_CACHE_DIR)


def install_text_ai_extension(version: str) -> None:
    raise NotImplementedError(
        "Implementation is waiting for decision on where the releases will be hosted."
    )
