# pylint: skip-file
# Importing cython packages causes import errors in pylint, we need to investigate this later
# see https://github.com/exasol/notebook-connector/issues/206

import importlib.metadata
import os
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Optional,
)

from exasol.ai.text.deployment import license_deployment as txai_licenses
from exasol.ai.text.deployment.script_deployer import create_scripts
from exasol.ai.text.deployment.txaie_language_container_deployer import (
    TXAIELanguageContainerDeployer,
)
from exasol.ai.text.extraction import (
    AbstractExtraction,
)
from exasol.ai.text.extraction.abstract_extraction import (
    Defaults,
)
from exasol.ai.text.extraction.extraction import Extraction as TextAiExtraction
from exasol.ai.text.extractors.bucketfs_model_repository import BucketFSRepository
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


def interactive_usage() -> bool:
    return os.environ.get("INTERACTIVE", "True").lower() == "true"


def install_model(conf: Secrets, model: TransformerModel) -> None:
    """
    Download and install the specified Huggingface model.
    """
    bucketfs_location = open_bucketfs_location(conf) / PATH_IN_BUCKET
    bfs_subdir = conf.txaie_models_bfs_dir
    with yaspin(text=f"- Huggingface model {model.name}") as spinner:
        if not interactive_usage():
            spinner.hide()
        download_transformers_model(
            bucketfs_location=bucketfs_location,
            sub_dir=bfs_subdir,
            task_type=model.task_type,
            model_name=model.name,
            model_factory=model.factory,
        )
    spinner.ok(CHECKMARK)


def deploy_license(
    conf: Secrets,
    license_content: Optional[str] = None,
    license_file: Optional[Path] = None,
) -> None:
    """
    Deploys the given license and saves its identifier to the secret store. The licence can either be
    defined by a path pointing to a licence file, or by the licence content given as a string.
    Parameters:
        conf:
            The secret store.
        licence_content:
            Optional. Content of a licence given as a string.
        licence_file:
            Optional. Path of a licence file.

    """

    license_content = license_content or txai_licenses.COMMUNITY_LICENSE
    if license_file:
        license_content = license_file.read_text()

    pyexasol_connection = open_pyexasol_connection(conf)
    txai_licenses.create_connection(pyexasol_connection, license_content)


def initialize_text_ai_extension(
    conf: Secrets,
    container_file: Optional[Path] = None,
    version: Optional[str] = None,
    install_slc: bool = True,
    install_scripts: bool = True,
    install_models: bool = True,
    install_bfs_credentials: bool = True,
    allow_override_language_alias: bool = True,
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
        install_slc:
            If True runs deployment of the locally stored Script Language Container file for the Text-AI Extension.
        install_scripts:
            If True runs deployment of Text-AI Extension scripts.
        install_models:
            If True uploads default Transformers models to the BucketFS.
        install_bfs_credentials:
            If set to False will skip the creation of the text ai specific database connection
            object encapsulating the BucketFS credentials.
        allow_override_language_alias:
            If True allows overriding the language definition.
    """

    def deploy_slc(container_file=None, version=None):
        container_url = version and TXAIELanguageContainerDeployer.slc_download_url(
            version
        )
        deploy_language_container(
            conf,
            container_name=TXAIELanguageContainerDeployer.SLC_NAME,
            container_file=container_file,
            container_url=container_url,
            language_alias=LANGUAGE_ALIAS,
            activation_key=ACTIVATION_KEY,
            path_in_bucket=PATH_IN_BUCKET,
            allow_override=allow_override_language_alias,
        )

    db_user = conf.get(CKey.db_user)
    bfs_conn_name = f"{BFS_CONNECTION_PREFIX}_{db_user}"

    print(f"Text AI: Updating Secure Configuration Storage")
    conf.save(CKey.txaie_bfs_connection, bfs_conn_name)
    conf.save(CKey.txaie_models_bfs_dir, BFS_MODELS_DIR)
    conf.save(CKey.txaie_models_cache_dir, MODELS_CACHE_DIR)

    if install_slc:
        print("Text AI: Downloading and installing Script Language Container (SLC)")
        if container_file:
            deploy_slc(container_file=container_file)
        else:
            version = version or importlib.metadata.version("exasol_text_ai_extension")
            deploy_slc(version=version)

    if install_models:
        #  Install default Hugging Face models into the Bucketfs using
        #  Transformers Extensions upload model functionality.
        print("Text AI: Downloading and installing Huggingface models to BucketFS:")
        install_model(
            conf,
            TransformerModel(
                DEFAULT_FEATURE_EXTRACTION_MODEL, "feature-extraction", AutoModel
            ),
        )
        install_model(
            conf,
            TransformerModel(
                DEFAULT_NAMED_ENTITY_MODEL,
                "token-classification",
                AutoModelForTokenClassification,
            ),
        )
        install_model(
            conf,
            TransformerModel(
                DEFAULT_NLI_MODEL,
                "zero-shot-classification",
                AutoModelForSequenceClassification,
            ),
        )

    if install_scripts:
        print("Text AI: Creating Scripts")
        pyexasol_connection = open_pyexasol_connection(
            conf, schema=conf.get(CKey.db_schema)
        )
        create_scripts(pyexasol_connection)

    if install_bfs_credentials:
        print(f"Text AI: Creating BFS connection {bfs_conn_name}")
        encapsulate_bucketfs_credentials(
            conf, path_in_bucket=PATH_IN_BUCKET, connection_name=bfs_conn_name
        )
    print(f"Text AI: Installation finished.")


class Extraction(AbstractExtraction):
    def defaults_with_model_repository(self, conf: Secrets) -> Defaults:
        if self.defaults.model_repository:
            return self.defaults
        model_repository = BucketFSRepository(
            connection_name=conf.txaie_bfs_connection,
            sub_dir=conf.txaie_models_bfs_dir,
        )
        return Defaults(
            parallelism_per_node=self.defaults.parallelism_per_node,
            batch_size=self.defaults.batch_size,
            model_repository=model_repository,
        )

    def run(self, conf: Secrets) -> None:
        activation_sql = get_activation_sql(conf)
        defaults = self.defaults_with_model_repository(conf)
        with open_pyexasol_connection(conf, compression=True) as connection:
            connection.execute(query=activation_sql)
            TextAiExtraction(
                extractor=self.extractor,
                output=self.output,
                defaults=defaults,
            ).run(
                pyexasol_con=connection,
                temporary_db_object_schema=conf.db_schema,
                language_alias=LANGUAGE_ALIAS,
            )
