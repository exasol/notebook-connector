from exasol.connections import open_pyexasol_connection
from exasol.secret_store import Secrets
from exasol.utils import optional_str_to_bool
from exasol.ai_lab_config import AILabConfig as CKey


def str_to_bool(conf: Secrets, key: CKey, default_value: bool) -> bool:
    """
    Tries to read a binary (i.e. yes/no) value from the secret store. If found
    returns the correspondent boolean. Otherwise, returns the provided default
    value.

    Parameters:
        conf:
            The secret store.
        key:
            The binary value key in the secret store.
        default_value:
            Default value if the key is not in the secret store.
    """
    prop_value = optional_str_to_bool(conf.get(key))
    return default_value if prop_value is None else prop_value


def encapsulate_bucketfs_credentials(
    conf: Secrets, path_in_bucket: str, connection_name: str
) -> None:
    """
    Creates a connection object in the database encapsulating
    a location in the bucket-fs and bucket-fs access credentials.

    Parameters:
        conf:
            The secret store. The store must hold the bucket-fs service
            parameters (BUCKETFS_HOST_NAME or EXTERNAL_HOST_NAME, BUCKETFS_PORT,
            BUCKETFS_SERVICE), the access credentials (BUCKETFS_USER,
            BUCKETFS_PASSWORD), and the bucket name (BUCKETFS_BUCKET), as well
            as the DB connection parameters.
        path_in_bucket:
            Path identifying a location in the bucket.
        connection_name:
            Name for the connection object to be created.
    """

    bfs_host = conf.get(CKey.bfs_host_name, conf.get(CKey.db_host_name))
    # For now, just use the http. Once the exasol.bucketfs is capable of using
    # the https without validating the server certificate choose between the
    # http and https depending on the BUCKETFS_ENCRYPTION setting, like this:
    # bfs_protocol = "https" if str_to_bool(conf, 'BUCKETFS_ENCRYPTION', True)
    # else "http"
    bfs_protocol = "http"
    bfs_dest = (
        f"{bfs_protocol}://{bfs_host}:{conf.get(CKey.bfs_port)}/"
        f"{conf.get(CKey.bfs_bucket)}/{path_in_bucket};{conf.get(CKey.bfs_service)}"
    )

    sql = f"""
    CREATE OR REPLACE CONNECTION [{connection_name}]
        TO '{bfs_dest}'
        USER {{BUCKETFS_USER!s}}
        IDENTIFIED BY {{BUCKETFS_PASSWORD!s}}
    """
    query_params = {
        "BUCKETFS_USER": conf.get(CKey.bfs_user),
        "BUCKETFS_PASSWORD": conf.get(CKey.bfs_password),
    }
    with open_pyexasol_connection(conf, compression=True) as conn:
        conn.execute(query=sql, query_params=query_params)


def encapsulate_huggingface_token(conf: Secrets, connection_name: str) -> None:
    """
    Creates a connection object in the database encapsulating a Huggingface token.

    Parameters:
        conf:
            The secret store. The store must hold the Huggingface token (HF_TOKEN),
             as well as the DB connection parameters.
        connection_name:
            Name for the connection object to be created.
    """

    sql = f"""
    CREATE OR REPLACE CONNECTION [{connection_name}]
        TO ''
        IDENTIFIED BY {{TOKEN!s}}
    """
    query_params = {"TOKEN": conf.get(CKey.huggingface_token)}
    with open_pyexasol_connection(conf, compression=True) as conn:
        conn.execute(query=sql, query_params=query_params)


def encapsulate_aws_credentials(conf: Secrets, connection_name: str) -> None:
    """
    Creates a connection object in the database encapsulating the address of
    an AWS S3 bucket and AWS access credentials.

    Parameters:
        conf:
            The secret store. The store must hold the S3 bucket parameters
            (AWS_BUCKET, AWS_REGION) and AWS access credentials (AWS_ACCESS_KEY_ID,
            AWS_SECRET_ACCESS_KEY), as well as the DB connection parameters.
        connection_name:
            Name for the connection object to be created.
    """

    sql = f"""
    CREATE OR REPLACE  CONNECTION [{connection_name}]
        TO 'https://{conf.get(CKey.aws_bucket)}.s3.{conf.get(CKey.aws_region)}.amazonaws.com/'
        USER {{ACCESS_ID!s}}
        IDENTIFIED BY {{SECRET_KEY!s}}
    """
    query_params = {
        "ACCESS_ID": conf.get(CKey.aws_access_key_id),
        "SECRET_KEY": conf.get(CKey.aws_secret_access_key),
    }
    with open_pyexasol_connection(conf, compression=True) as conn:
        conn.execute(query=sql, query_params=query_params)
