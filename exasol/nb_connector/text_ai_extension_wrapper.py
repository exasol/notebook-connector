import importlib.metadata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import exasol.bucketfs as bfs  # type: ignore
from exasol.ai.text.deployment.script_deployer import create_scripts
from exasol.ai.text.deployment.txaie_language_container_deployer import TXAIELanguageContainerDeployer
from exasol.ai.text.deployment import license_deployment as txai_licenses
from exasol.ai.text.extraction.abstract_extraction import Output
from exasol.ai.text.extraction.extraction import (
    AbstractExtraction,
    Extraction as TextAiExtraction,
)
from exasol.ai.text.extractors.default_models import (
    DEFAULT_FEATURE_EXTRACTION_MODEL,
    DEFAULT_NAMED_ENTITY_MODEL,
    DEFAULT_NLI_MODEL,
)
from exasol.ai.text.impl.utils.transformers_utils import download_transformers_model
from transformers import (
    AutoModel,
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
)
from yaspin import yaspin

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.connections import (
    open_bucketfs_location,
    open_pyexasol_connection,
)
from exasol.nb_connector.extension_wrapper_common import (
    deploy_language_container,
    encapsulate_bucketfs_credentials,
)
from exasol.nb_connector.language_container_activation import (
    ACTIVATION_KEY_PREFIX,
    get_activation_sql,
)
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

CHECKMARK = "\u2705"
"""
Checkmark symbol for signalling success after an operation using an
animated spinner from https://github.com/pavdmyt/yaspin.
"""

@dataclass
class TransformerModel:
    name: str
    task_type: str
    factory: Any


class ModelInstaller:
    """
    Download Huggingface models and deploy them to Exasol BucketFS.
    """
    def __init__(self, bucketfs_location: bfs.path.PathLike, bfs_subdir: str):
        self.bucketfs_location = bucketfs_location
        self.bfs_subdir = bfs_subdir
        self.models = [
            TransformerModel(
                DEFAULT_FEATURE_EXTRACTION_MODEL,
                "feature-extraction",
                AutoModel,
            ),
            TransformerModel(
                DEFAULT_NAMED_ENTITY_MODEL,
                "token-classification",
                AutoModelForTokenClassification,
            ),
            TransformerModel(
                DEFAULT_NLI_MODEL,
                "zero-shot-classification",
                AutoModelForSequenceClassification,
            ),
        ]

    def download_and_install(self) -> None:
        for model in self.models:
            with yaspin(text=f"- Huggingface model {model}") as spinner:
                download_transformers_model(
                    bucketfs_location=self.bucketfs_location,
                    sub_dir=self.bfs_subdir,
                    task_type=model.task_type,
                    model_name=model.name,
                    model_factory=model.factory
                )
            spinner.ok(CHECKMARK)


def deploy_license(
    conf: Secrets,
    # license_file: Optional[Path] = None,
    license_content: Optional[str] = None,
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

    license_content = license_content or txai_licenses.COMMUNITY_LICENSE
    # if license_content:
    #     pass
    # elif license_file:
    #     license_content = license_file.read_text()
    # else:
    #     license_content = txai_licenses.COMMUNITY_LICENSE

    pyexasol_connection = open_pyexasol_connection(conf)
    txai_licenses.create_connection(pyexasol_connection, license_content)


@dataclass
class InstallOptions:
    slc: bool = True
    udf_scripts: bool = False
    models: bool = False
    bfs_credentials: bool = True


def initialize_text_ai_extension(
    conf: Secrets,
    container_file: Optional[Path] = None,
    version: Optional[str] = None,
    language_alias: str = LANGUAGE_ALIAS,
    run_deploy_container: bool = True, # proposal: rename to install_slc
    run_deploy_scripts: bool = False, # proposal: rename to install_udf_scripts
    run_upload_models: bool = False, # proposal: rename to install_models
    run_encapsulate_bfs_credentials: bool = True, # proposal: rename to install_bfs_credentials
    # alternatively we could pass an instance of InstallOptions
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

    def install_slc(version=None, container_file=None):
        container_url = version and TXAIELanguageContainerDeployer.slc_download_url(version)
        deploy_language_container(
            conf,
            container_name=TXAIELanguageContainerDeployer.SLC_NAME,
            container_file=container_file,
            container_url=container_url,
            language_alias=language_alias,
            activation_key=ACTIVATION_KEY,
            path_in_bucket=PATH_IN_BUCKET,
            allow_override=allow_override,
        )

    # Create the name of the Exasol connection to the BucketFS
    db_user = conf.get(CKey.db_user)
    bfs_conn_name = f"{BFS_CONNECTION_PREFIX}_{db_user}"

    if run_deploy_container:
        print("Text AI: Downloading and installing Script Language Container (SLC)")
        if version:
            install_slc(version)
            # Can run_upload_models, run_deploy_scripts,
            # run_encapsulate_bfs_credentials, etc. be ignored here?
            return

        if container_file:
            install_slc(container_file=container_file)
        else:
            version = importlib.metadata.version("exasol_text_ai_extension")
            install_slc(version)

    if run_upload_models:
        #  Install default Hugging Face models into the Bucketfs using
        #  Transformers Extensions upload model functionality.
        print("Text AI: Downloading and installing Huggingface models to BucketFS:")
        bucketfs_location = open_bucketfs_location(conf) / PATH_IN_BUCKET
        ModelInstaller(
            bucketfs_location=bucketfs_location,
            bfs_subdir=conf.txaie_models_bfs_dir,
        ).download_and_install()

    if run_deploy_scripts:
        print("Text AI: Creating UDF scripts")
        pyexasol_connection = open_pyexasol_connection(conf, schema=conf.get(CKey.db_schema))
        create_scripts(pyexasol_connection)

    if run_encapsulate_bfs_credentials:
        print(f"Text AI: Creating BFS connection {bfs_conn_name}")
        encapsulate_bucketfs_credentials(
            conf, path_in_bucket=PATH_IN_BUCKET, connection_name=bfs_conn_name
        )

    # Update configuration
    print(f"Text AI: Updating Secure Configuration Storage")
    conf.save(CKey.txaie_bfs_connection, bfs_conn_name)
    conf.save(CKey.txaie_models_bfs_dir, BFS_MODELS_DIR)
    conf.save(CKey.txaie_models_cache_dir, MODELS_CACHE_DIR)
    print(f"Text AI: Installation finished.")


class Extraction(AbstractExtraction):
    def run(self, conf: Secrets) -> None:
        activation_sql = get_activation_sql(conf)
        with open_pyexasol_connection(conf, compression=True) as connection:
            connection.execute(query=activation_sql)
            TextAiExtraction(
                extractor=self.extractor,
                output=self.output,
                defaults=self.defaults,
            ).run(
                pyexasol_con=connection,
                temporary_db_object_schema=conf.db_schema,
                language_alias=LANGUAGE_ALIAS,
            )
