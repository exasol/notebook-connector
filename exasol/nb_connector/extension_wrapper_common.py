from __future__ import annotations
from typing import Optional

import exasol.bucketfs as bfs   # type: ignore

from exasol.nb_connector.connections import (open_pyexasol_connection,
                                             get_backend, get_saas_database_id)
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.utils import optional_str_to_bool
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey, StorageBackend


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
    a location in the BucketFS and BucketFS access credentials.

    Parameters:
        conf:
            The secret store.
            For an On-Prem database the store must hold the BucketFS service
            parameters (bfs_host_name or db_host_name, bfs_port,
            bfs_service), the access credentials (bfs_user,
            bfs_password), and the bucket name (bfs_bucket), as well
            as the DB connection parameters.
            For a SaaS database the store must hold the SaaS connection
            parameters (saas_url, saas_account_id, saas_database_id or
            saas_database_name, saas_token).
        path_in_bucket:
            Path identifying a location in the bucket.
        connection_name:
            Name for the connection object to be created.

    The parameters will be stored in json strings. The distribution
    of the parameters among the connection entities will be as following.
    On-Prem:
        TO: backend, url, service_name, bucket_name, verify, path
        USER: username
        IDENTIFIED BY: password
    SaaS:
        TO: backend, url, account_id, path
        USER: database_id
        IDENTIFIED BY: pat

    Note that the parameter names correspond to the arguments of the build_path
    function. provided by the bucketfs-python. Hence, the most convenient way to
    handle this lot is to combine json structures from all three entities and
    pass them as kwargs to the build_path. The code below gives a usage example.

    bfs_params = json.loads(conn_obj.address)
    bfs_params.update(json.loads(conn_obj.user))
    bfs_params.update(json.loads(conn_obj.password))
    bfs_path = build_path(**bfs_params)

    A note about handling the TLS certificate verification settings.
    If the server certificate verification is turned on, either through
    reliance of the default https request settings or by setting the cert_vld
    configuration parameter to True, this intention will be passed to
    the connection object. However, if the user specifies a custom CA list
    file or directory, which also implies the certificate verification,
    the connection object will instead turn the verification off. This is
    because there is no guarantee that the consumer of the connection object,
    i.e. a UDF, would have this custom CA list, and even if it would, its location
    is unknown. This is only applicable for an On-Prem backend.
    """

    def to_json_str(**kwargs) -> str:
        def format_value(v):
            return f'"{v}"' if isinstance(v, str) else v

        return ", ".join(f'"{k}":{format_value(v)}' for k, v in kwargs.items()
                         if v is not None)

    backend = get_backend(conf)
    if backend == StorageBackend.onprem:
        host = conf.get(CKey.bfs_host_name, conf.get(CKey.db_host_name))
        protocol = "https" if str_to_bool(conf, CKey.bfs_encryption, True) else "http"
        url = f"{protocol}://{host}:{conf.get(CKey.bfs_port)}"
        verify: Optional[bool] = (False if conf.get(CKey.trusted_ca)
                                  else optional_str_to_bool(conf.get(CKey.cert_vld)))
        conn_to = to_json_str(backend=bfs.path.StorageBackend.onprem.name,
                              url=url, service_name=conf.get(CKey.bfs_service),
                              bucket_name=conf.get(CKey.bfs_bucket),
                              path=path_in_bucket,
                              verify=verify)
        conn_user = to_json_str(username=conf.get(CKey.bfs_user))
        conn_password = to_json_str(password=conf.get(CKey.bfs_password))
    else:
        database_id = get_saas_database_id(conf)
        conn_to = to_json_str(backend=bfs.path.StorageBackend.saas.name,
                              url=conf.get(CKey.saas_url),
                              account_id=conf.get(CKey.saas_account_id),
                              path=path_in_bucket)
        conn_user = to_json_str(database_id=database_id)
        conn_password = to_json_str(pat=conf.get(CKey.saas_token))

    sql = f"""
    CREATE OR REPLACE CONNECTION [{connection_name}]
        TO {{BUCKETFS_ADDRESS!s}}
        USER {{BUCKETFS_USER!s}}
        IDENTIFIED BY {{BUCKETFS_PASSWORD!s}}
    """
    query_params = {
        "BUCKETFS_ADDRESS": conn_to,
        "BUCKETFS_USER": conn_user,
        "BUCKETFS_PASSWORD": conn_password
    }
    with open_pyexasol_connection(conf, compression=True) as conn:
        conn.execute(query=sql, query_params=query_params)


def encapsulate_huggingface_token(conf: Secrets, connection_name: str) -> None:
    """
    Creates a connection object in the database encapsulating a Huggingface token.

    Parameters:
        conf:
            The secret store. The store must hold the Huggingface token (huggingface_token),
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


def encapsulate_aws_credentials(conf: Secrets, connection_name: str,
                                s3_bucket_key: CKey) -> None:
    """
    Creates a connection object in the database encapsulating the address of
    an AWS S3 bucket and AWS access credentials.

    Parameters:
        conf:
            The secret store. The store must hold the S3 bucket parameters
            (aws_bucket, aws_region) and AWS access credentials (aws_access_key_id,
            aws_secret_access_key), as well as the DB connection parameters.
        connection_name:
            Name for the connection object to be created.
        s3_bucket_key:
            The secret store key of the AWS S3 bucket name.
    """

    sql = f"""
    CREATE OR REPLACE  CONNECTION [{connection_name}]
        TO 'https://{conf.get(s3_bucket_key)}.s3.{conf.get(CKey.aws_region)}.amazonaws.com/'
        USER {{ACCESS_ID!s}}
        IDENTIFIED BY {{SECRET_KEY!s}}
    """
    query_params = {
        "ACCESS_ID": conf.get(CKey.aws_access_key_id),
        "SECRET_KEY": conf.get(CKey.aws_secret_access_key),
    }
    with open_pyexasol_connection(conf, compression=True) as conn:
        conn.execute(query=sql, query_params=query_params)
