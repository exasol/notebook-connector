from typing import Optional, Generator
from contextlib import contextmanager
from pathlib import Path
import requests
import subprocess
import tempfile

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey

LANGUAGE_ALIAS = "PYTHON3_TXAIE"

LATEST_KNOWN_VERSION = "???"


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

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        # Save the downloaded zip in a temporary file
        for chunk in response.iter_content(chunk_size=1048576):
            tmp_file.write(chunk)
        tmp_file.close()
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Unzip the file into a temporary directory
            unzip_cmd = ["unzip", "-q", "-P", zip_password, tmp_file.name, "-d", tmp_dir]
            subprocess.run(unzip_cmd, check=True, capture_output=True)
            tmp_path = Path(tmp_dir)
            # Find and return the project wheel and the SLC
            project_wheel = next(tmp_path.glob("*.whl"))
            slc_tar_gz = next(tmp_path.glob("*.tar.gz"))
            yield project_wheel, slc_tar_gz


def deploy_licence(conf: Secrets,
                   licence_file: Optional[Path] = None,
                   licence_content: Optional[str] = None) -> None:
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
    pass


def initialize_text_ai_extension(conf: Secrets,
                                 container_file: Optional[Path] = None,
                                 version: Optional[str] = LATEST_KNOWN_VERSION,
                                 language_alias: str = LANGUAGE_ALIAS,
                                 run_deploy_container: bool = True,
                                 run_deploy_scripts: bool = True,
                                 run_upload_models: bool = True,
                                 run_encapsulate_bfs_credentials: bool = True,
                                 allow_override: bool = True) -> None:
    """
    Depending on which flags are set, runs different steps to install Text-AI Extension in the DB.
    Possible steps:

    * Call the Text-AI Extension's language container deployment API.
    If given a version, downloads the specified released version of the extension from ???
    and uploads it to the BucketFS.

    If given a container_file path instead, installs the given container in the Bucketfs.

    If neither is given, attempts to install the latest version from ???.

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
    pass
