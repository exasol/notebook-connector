from exasol_sagemaker_extension.deployment.deploy_create_statements import DeployCreateStatements   # type: ignore
from exasol_sagemaker_extension.deployment.language_container_deployer import LanguageActivationLevel   # type: ignore
from exasol_sagemaker_extension.deployment.sme_language_container_deployer import SmeLanguageContainerDeployer  # type: ignore

from exasol.connections import (
    get_external_host,
    open_pyexasol_connection,
)
from exasol.extension_wrapper_common import (
    encapsulate_aws_credentials,
    str_to_bool
)
from exasol.language_container_activation import (
    ACTIVATION_KEY_PREFIX,
    get_activation_sql
)
from exasol.secret_store import Secrets

# Root directory in a bucket-fs bucket where all stuff of the Sagemaker
# Extension, including its language container, will be uploaded.
PATH_IN_BUCKET = "SME"

LATEST_KNOWN_VERSION = "0.6.0"

# Activation SQL for the Sagemaker Extension will be saved in the secret
# store with this key.
ACTIVATION_KEY = ACTIVATION_KEY_PREFIX + "sme"

# Name of the connection object with AWS credentials and S3 location
# will be saved in the secret store with this key.
AWS_CONNECTION_KEY = "SME_AWS_CONN"

# Name of the connection object with AWS credentials and S3 location
# will be prefixed with this string.
AWS_CONNECTION_PREFIX = "SME_AWS"


def deploy_language_container(conf: Secrets, version: str) -> None:
    """
    Calls the Sagemaker Extension's language container deployment API.
    Downloads the specified released version of the extension from the GitHub
    and uploads it to the BucketFS.

    This function doesn't activate the language container. Instead, it gets the
    activation SQL using the same API and writes it to the secret store. The
    name of the key is defined in the ACTIVATION_KEY constant.

    This function will eventually be shared between different extension
    wrappers, once the language container deployment functionality is moved
    from extensions to the script-language-container-tool repo.

    Parameters:
        conf:
            The secret store. The store must contain the DB connection parameters
            and the parameters of the bucket-fs service.
        version:
            Sagemaker Extension version.
    """

    deployer = SmeLanguageContainerDeployer.create(
        dsn=get_external_host(conf),
        db_user=conf.USER,
        db_password=conf.PASSWORD,
        bucketfs_name=conf.BUCKETFS_SERVICE,
        bucketfs_host=conf.get("BUCKETFS_HOST_NAME", conf.EXTERNAL_HOST_NAME),
        bucketfs_port=int(conf.BUCKETFS_PORT),
        bucketfs_user=conf.BUCKETFS_USER,
        bucketfs_password=conf.BUCKETFS_PASSWORD,
        bucketfs_use_https=str_to_bool(conf, "BUCKETFS_ENCRYPTION", True),
        bucket=conf.BUCKETFS_BUCKET,
        path_in_bucket=PATH_IN_BUCKET,
        use_ssl_cert_validation=str_to_bool(conf, "CERTIFICATE_VALIDATION", True),
        ssl_trusted_ca=conf.get("TRUSTED_CA"),
        ssl_client_certificate=conf.get("CLIENT_CERTIFICATE"),
        ssl_private_key=conf.get("PRIVATE_KEY"),
    )

    # Install the language container.
    deployer.download_from_github_and_run(version, False)

    # Save the activation SQL in the secret store.
    activation_sql = deployer.generate_activation_command(
        deployer.SLC_NAME, LanguageActivationLevel.Session
    )
    conf.save(ACTIVATION_KEY, activation_sql)


def deploy_scripts(conf: Secrets) -> None:
    """
    Deploys all the extension's scripts to the database.

    Parameters:
        conf:
            The secret store. The store should contain the language activation
            SQL command. This command should be created during the language
            container deployment. The store should also have the DB schema.
    """

    with open_pyexasol_connection(conf, compression=True) as conn:
        # First need to activate the language container at the session level.
        activation_sql = get_activation_sql(conf)
        conn.execute(activation_sql)

        scripts_deployer = DeployCreateStatements(
            exasol_conn=conn, schema=conf.SCHEMA, to_print=False, develop=False
        )
        scripts_deployer.run()


def initialize_sme_extension(conf: Secrets,
                             version: str = LATEST_KNOW_VERSION,
                             run_deploy_container: bool = True,
                             run_deploy_scripts: bool = True,
                             run_encapsulate_aws_credentials: bool = True) -> None:
    """
    Performs all necessary operations to get the Sagemaker Extension
    up and running. See the "Getting Started" and "Setup" sections of the
    extension's User Guide for details.

    Parameters:
        conf:
            The secret store. The store should contain all the required
            parameters for accessing the database, bucket-fs and AWS.
        version:
            Sagemaker Extension version. If not specified the hardcoded
            latest known version will be used.
        run_deploy_container:
            If set to False will skip the language container deployment.
        run_deploy_scripts:
            If set to False will skip the deployment of the scripts.
        run_encapsulate_aws_credentials:
            If set to False will skip the creation of the database connection
            object encapsulating the AWS credentials.
    """

    # Make the connection object name
    aws_conn_name = "_".join([AWS_CONNECTION_PREFIX, conf.USER])

    if run_deploy_container:
        deploy_language_container(conf, version)

    # Create the required objects in the database
    if run_deploy_scripts:
        deploy_scripts(conf)
    if run_encapsulate_aws_credentials:
        encapsulate_aws_credentials(conf, aws_conn_name)

    # Save the connection object name in the secret store.
    conf.save(AWS_CONNECTION_KEY, aws_conn_name)
