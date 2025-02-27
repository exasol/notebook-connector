from exasol.nb_connector.secret_store import Secrets
from pathlib import Path

LANGUAGE_ALIAS = "PYTHON3_TXAIE"

LATEST_KNOWN_VERSION = "???"

def deploy_licence(conf: Secrets,
                   licence_file: Path = None,
                   licence_content: str = None) -> None:
    """
    Deploys the given license and saves its identifier to the secret store. The licence can either be
    defined by a path pointing to a licence file, or by the licence content given as a string.
    Parameters:
         conf:
            The secret store.
        licence_file:
            Path of a licence file.
        licence_content:
            Content of a licence given as a string.

    """
    pass

def initialize_text_ai_extension(conf: Secrets,
                                 container_file: Path,
                                 version: str = LATEST_KNOWN_VERSION,
                                 language_alias: str = LANGUAGE_ALIAS,
                                 run_deploy_container: bool = True,
                                 run_deploy_scripts: bool = True,
                                 run_upload_models: bool = True,
                                 allow_override: bool = True) -> None:
    """
    Depending on which flags are set, runs different steps to install Text-AI Extension in the DB.
    Possible steps:

    * Call the Text-AI Extension's language container deployment API.
    Downloads the specified released version of the extension from ???
    and uploads it to the BucketFS.

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
            Path pointing to the locally stored Script Language Container file for the Text-AI Extension.
        version:
            Text-AI extension version.
        language_alias:
            The language alias of the extension's language container.
        run_deploy_container:
            If True runs deployment of the locally stored Script Language Container file for the Text-AI Extension.
        run_deploy_scripts:
            If True runs deployment of Text-AI Extension scripts.
        run_upload_models:
            If True uploads default Transformers models to the BucketFS.
        allow_override:
            If True allows overriding the language definition.
    """
    pass
