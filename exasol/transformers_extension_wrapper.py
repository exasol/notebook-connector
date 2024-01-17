from exasol_transformers_extension.utils.bucketfs_operations import get_model_path  # type: ignore
from exasol_transformers_extension.utils.bucketfs_operations import upload_model_files_to_bucketfs  # type: ignore
from exasol_transformers_extension.utils.bucketfs_operations import create_bucketfs_location    # type: ignore

from exasol_transformers_extension.deployment.language_container_deployer import LanguageActivationLevel    # type: ignore
from exasol_transformers_extension.deployment.scripts_deployer import ScriptsDeployer   # type: ignore
from exasol_transformers_extension.deployment.te_language_container_deployer import TeLanguageContainerDeployer     # type: ignore

# TODO: Disable this mypy "missing imports" nonsense.

from exasol.connections import (
    get_external_host,
    open_pyexasol_connection
)
from exasol.extension_wrapper_common import (
    encapsulate_bucketfs_credentials,
    encapsulate_huggingface_token,
    str_to_bool
)
from exasol.language_container_activation import (
    ACTIVATION_KEY_PREFIX,
    get_activation_sql
)
from exasol.secret_store import Secrets
from exasol.ai_lab_config import AILabConfig as CKey

# Root directory in a BucketFS bucket where all stuff of the Transformers
# Extension, including its language container, will be uploaded.
PATH_IN_BUCKET = "TE"

LANGUAGE_ALIAS = "PYTHON3_TE"

LATEST_KNOWN_VERSION = "0.7.0"

# Activation SQL for the Transformers Extension will be saved in the secret
# store with this key.
ACTIVATION_KEY = ACTIVATION_KEY_PREFIX + "te"

# The name of the connection object with BucketFS location and credentials
# will be prefixed with this string.
BFS_CONNECTION_PREFIX = "TE_BFS"

# Models will be uploaded into this directory in BucketFS.
BFS_MODELS_DIR = 'te_models'

# The name of the connection object with a Huggingface token will be prefixed
# with this string.
HF_CONNECTION_PREFIX = "TE_HF"

# Models downloaded from the Huggingface archive to a local drive will be
# cached in this directory.
MODELS_CACHE_DIR = "models_cache"


def deploy_language_container(conf: Secrets,
                              version: str,
                              language_alias: str) -> None:
    """
    Calls the Transformers Extension's language container deployment API.
    Downloads the specified released version of the extension from the GitHub
    and uploads it to the BucketFS.

    This function doesn't activate the language container. Instead, it gets the
    activation SQL using the same API and writes it to the secret store. The name
    of the key is defined in the ACTIVATION_KEY constant.

    This function will eventually be shared between different extension wrappers,
    once the language container deployment functionality is moved to the
    script-language-container-tool repo.

    Parameters:
        conf:
            The secret store. The store must contain the DB connection parameters
            and the parameters of the BucketFS service.
        version:
            Transformers Extension version.
        language_alias:
            The language alias of the extension's language container.
    """

    deployer = TeLanguageContainerDeployer.create(
        dsn=get_external_host(conf),
        db_user=conf.get(CKey.db_user),
        db_password=conf.get(CKey.db_password),
        bucketfs_name=conf.get(CKey.bfs_service),
        bucketfs_host=conf.get(CKey.bfs_host_name, conf.get(CKey.db_host_name)),
        bucketfs_port=int(str(conf.get(CKey.bfs_port))),
        bucketfs_user=conf.get(CKey.bfs_user),
        bucketfs_password=conf.get(CKey.bfs_password),
        bucketfs_use_https=str_to_bool(conf, CKey.bfs_encryption, True),
        bucket=conf.get(CKey.bfs_bucket),
        path_in_bucket=PATH_IN_BUCKET,
        language_alias=language_alias,
        use_ssl_cert_validation=str_to_bool(conf, CKey.cert_vld, True),
        ssl_trusted_ca=conf.get(CKey.trusted_ca),
        ssl_client_certificate=conf.get(CKey.client_cert),
        ssl_private_key=conf.get(CKey.client_key)
    )

    # Install the language container.
    deployer.download_from_github_and_run(version, False)

    # Save the activation SQL in the secret store.
    activation_sql = deployer.generate_activation_command(
        deployer.SLC_NAME, LanguageActivationLevel.Session
    )
    conf.save(ACTIVATION_KEY, activation_sql)


def deploy_scripts(conf: Secrets,
                   language_alias: str) -> None:
    """
    Deploys all the extension's scripts to the database.

    Parameters:
        conf:
            The secret store. The store should contain the language activation
            SQL command. This command should be created during the language
            container deployment. The store should also have the DB schema.
        language_alias:
            The language alias of the extension's language container.
    """

    with open_pyexasol_connection(conf, compression=True) as conn:
        # First need to activate the language container at the session level, otherwise the script creation fails.
        activation_sql = get_activation_sql(conf)
        conn.execute(activation_sql)

        scripts_deployer = ScriptsDeployer(language_alias, conf.get(CKey.db_schema), conn)
        scripts_deployer.deploy_scripts()


def initialize_te_extension(conf: Secrets,
                            version: str = LATEST_KNOWN_VERSION,
                            language_alias: str = LANGUAGE_ALIAS,
                            run_deploy_container: bool = True,
                            run_deploy_scripts: bool = True,
                            run_encapsulate_bfs_credentials: bool = True,
                            run_encapsulate_hf_token: bool = True) -> None:
    """
    Performs all necessary operations to get the Transformers Extension
    up and running. See the "Getting Started" and "Setup" sections of the
    extension's User Guide for details.

    Parameters:
        conf:
            The secret store. The store should contain all the required
            parameters for accessing the database and BucketFS.
        version:
            Transformers Extension version. If not specified the hardcoded
            latest known version will be used.
        language_alias:
            The language alias of the extension's language container. Normally
            this parameter would only be used for testing.
        run_deploy_container:
            If set to False will skip the language container deployment.
        run_deploy_scripts:
            If set to False will skip the deployment of the UDF scripts.
        run_encapsulate_bfs_credentials:
            If set to False will skip the creation of the database connection
            object encapsulating the BucketFS credentials.
        run_encapsulate_hf_token:
            If set to False will skip the creation of the database connection
            object encapsulating the Huggingface token.
    """

    # Make the connection object names
    db_user = str(conf.get(CKey.db_user))
    bfs_conn_name = "_".join([BFS_CONNECTION_PREFIX, db_user])
    token = conf.get(CKey.huggingface_token)
    hf_conn_name = "_".join([HF_CONNECTION_PREFIX, db_user]) if token else ""

    if run_deploy_container:
        deploy_language_container(conf, version, language_alias)

    # Create the required objects in the database
    if run_deploy_scripts:
        deploy_scripts(conf, language_alias)
    if run_encapsulate_bfs_credentials:
        encapsulate_bucketfs_credentials(
            conf, path_in_bucket=PATH_IN_BUCKET, connection_name=bfs_conn_name
        )
    if token and run_encapsulate_hf_token:
        encapsulate_huggingface_token(conf, hf_conn_name)

    # Save the connection object names in the secret store.
    conf.save(CKey.te_bfs_connection, bfs_conn_name)
    conf.save(CKey.te_hf_connection, hf_conn_name)
    # Save the directory names in the secret store
    conf.save(CKey.te_models_bfs_dir, BFS_MODELS_DIR)
    conf.save(CKey.te_models_cache_dir, MODELS_CACHE_DIR)


def upload_model_from_cache(
        conf: Secrets,
        model_name: str,
        cache_dir: str) -> None:
    """
    Uploads model previously downloaded and cached on a local drive. This,
    for instance, could have been done with the following code.

    from transformers import AutoTokenizer, AutoModel
    AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
    AutoModel.from_pretrained(model_name, cache_dir=cache_dir)

    Parameters:
        conf:
            The secret store.
        model_name:
            Name of the model at the Huggingface archive.
        cache_dir:
            Directory on the local drive where the model was cached. Each model
            should have its own cache directory.
    """

    # Create bucketfs location
    bfs_host = conf.get(CKey.bfs_host_name, conf.get(CKey.db_host_name))
    bucketfs_location = create_bucketfs_location(
        conf.get(CKey.bfs_service), bfs_host,
        int(str(conf.get(CKey.bfs_port))), str(conf.get(CKey.bfs_encryption)).lower() == 'true',
        conf.get(CKey.bfs_user), conf.get(CKey.bfs_password), conf.get(CKey.bfs_bucket),
        PATH_IN_BUCKET)

    # Upload the downloaded model files into bucketfs
    upload_path = get_model_path(conf.get(CKey.te_models_bfs_dir), model_name)
    upload_model_files_to_bucketfs(cache_dir, upload_path, bucketfs_location)


def upload_model(
        conf: Secrets,
        model_name: str,
        cache_dir: str,
        **kwargs) -> None:
    """
    Uploads model from the Huggingface hub or from the local cache in case it
    has already been downloaded from the hub. The user token, if found in the
    secret store will be passed to the Huggingface interface.

    Parameters:
        conf:
            The secret store.
        model_name:
            Name of the model at the Huggingface archive.
        cache_dir:
            Directory on the local drive where the model is to be cached.
            Each model should have its own cache directory.
        kwargs:
            Additional parameters to be passed to the `from_pretrained`
            methods of the AutoTokenizer and AutoModel. The user token, if specified
            here, will be used instead of the one in the secret store.
    """
    from transformers import AutoTokenizer, AutoModel   # type: ignore

    if 'token' not in kwargs:
        token = conf.get(CKey.huggingface_token)
        if token:
            kwargs['token'] = token

    AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir, **kwargs)
    AutoModel.from_pretrained(model_name, cache_dir=cache_dir, **kwargs)

    upload_model_from_cache(conf, model_name, cache_dir)
