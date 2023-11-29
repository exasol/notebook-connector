import ssl
from pathlib import Path
from typing import (
    Any,
    Optional,
)

import pyexasol  # type: ignore
import sqlalchemy  # type: ignore

import exasol.bucketfs as bfs  # type: ignore
from exasol.secret_store import Secrets


def _optional_str_to_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    value_l = value.lower()
    if value_l in ["y", "yes", "true"]:
        return True
    elif value_l in ["n", "no", "false"]:
        return False
    else:
        raise ValueError("Invalid boolean value " + value)


def _optional_encryption(conf: Secrets) -> Optional[bool]:
    return _optional_str_to_bool(conf.get("ENCRYPTION"))


def _extract_ssl_options(conf: Secrets) -> dict:
    """
    Extracts SSL parameters from the provided configuration.
    Returns a dictionary in the winsocket-client format
    (see https://websocket-client.readthedocs.io/en/latest/faq.html#what-else-can-i-do-with-sslopts)
    """
    sslopt: dict[str, object] = {}

    # Is server certificate validation required?
    certificate_validation = _optional_str_to_bool(conf.get("CERTIFICATE_VALIDATION"))
    if certificate_validation is not None:
        sslopt["cert_reqs"] = (
            ssl.CERT_REQUIRED if certificate_validation else ssl.CERT_NONE
        )

    # Is a bundle with trusted CAs provided?
    trusted_ca = conf.get("TRUSTED_CA")
    if trusted_ca:
        trusted_ca_path = Path(trusted_ca)
        if trusted_ca_path.is_dir():
            sslopt["ca_cert_path"] = trusted_ca
        elif trusted_ca_path.is_file():
            sslopt["ca_certs"] = trusted_ca
        else:
            raise ValueError(f"Trusted CA location {trusted_ca} doesn't exist.")

    # Is client's own certificate provided?
    client_certificate = conf.get("CLIENT_CERTIFICATE")
    if client_certificate:
        if not Path(client_certificate).is_file():
            raise ValueError(f"Certificate file {client_certificate} doesn't exist.")
        sslopt["certfile"] = client_certificate
        private_key = conf.get("PRIVATE_KEY")
        if private_key:
            if not Path(private_key).is_file():
                raise ValueError(f"Private key file {private_key} doesn't exist.")
            sslopt["keyfile"] = private_key

    return sslopt


def get_external_host(conf: Secrets) -> str:
    """Constructs the host part of a DB URL using provided configuration parameters."""
    return f"{conf.EXTERNAL_HOST_NAME}:{conf.DB_PORT}"


def get_udf_bucket_path(conf: Secrets) -> str:
    """
    Builds the path of the BucketFS bucket specified in the configuration,
    as it's seen in the udf's file system.
    """
    return f"/buckets/{conf.BUCKETFS_SERVICE}/{conf.BUCKETFS_BUCKET}"


def open_pyexasol_connection(conf: Secrets, **kwargs) -> pyexasol.ExaConnection:
    """
    Opens a pyexasol connection using provided configuration parameters.
    Does NOT set the default schema, even if it is defined in the configuration.

    Any additional parameters can be passed to pyexasol via the kwargs.
    Parameters in kwargs override the correspondent values in the configuration.

    The configuration should provide the following parameters:
    - Server address and port (EXTERNAL_HOST_NAME, DB_PORT),
    - Client security credentials (USER, PASSWORD).
    Optional parameters include:
    - Secured comm flag (ENCRYPTION),
    - Some of the SSL options (CERTIFICATE_VALIDATION, TRUSTED_CA, CLIENT_CERTIFICATE).
    If the schema is not provided then it should be set explicitly in every SQL statement.
    For other optional parameters the default settings are as per the pyexasol interface.
    """

    conn_params: dict[str, Any] = {
        "dsn": get_external_host(conf),
        "user": conf.USER,
        "password": conf.PASSWORD,
    }

    encryption = _optional_encryption(conf)
    if encryption is not None:
        conn_params["encryption"] = encryption
    ssopt = _extract_ssl_options(conf)
    if ssopt:
        conn_params["websocket_sslopt"] = ssopt

    conn_params.update(kwargs)

    return pyexasol.connect(**conn_params)


def open_sqlalchemy_connection(conf: Secrets):
    """
    Creates an Exasol SQLAlchemy websocket engine using provided configuration parameters.
    Does NOT set the default schema, even if it is defined in the configuration.

    The configuration should provide the following parameters:
    - Server address and port (EXTERNAL_HOST_NAME, DB_PORT),
    - Client security credentials (USER, PASSWORD).
    Optional parameters include:
    - Secured comm flag (ENCRYPTION).
    - Validation of the server's TLS/SSL certificate by the client (CERTIFICATE_VALIDATION).
    If the schema is not provided then it should be set explicitly in every SQL statement.
    For other optional parameters the default settings are as per the Exasol SQLAlchemy interface.
    Currently, it's not possible to use a bundle of trusted CAs other than the default. Neither
    it is possible to set the client TLS/SSL certificate.
    """

    websocket_url = (
        f"exa+websocket://{conf.USER}:{conf.PASSWORD}@{get_external_host(conf)}"
    )

    delimiter = "?"
    encryption = _optional_encryption(conf)
    if encryption is not None:
        websocket_url = (
            f'{websocket_url}{delimiter}ENCRYPTION={"Yes" if encryption else "No"}'
        )
        delimiter = "&"

    certificate_validation = _extract_ssl_options(conf).get("cert_reqs")
    if (certificate_validation is not None) and (not certificate_validation):
        websocket_url = f"{websocket_url}{delimiter}SSLCertificate=SSL_VERIFY_NONE"

    return sqlalchemy.create_engine(websocket_url)


def open_bucketfs_connection(conf: Secrets) -> bfs.Bucket:
    """
    Connects to a BucketFS service using provided configuration parameters.
    Returns the Bucket object for the bucket selected in the configuration.

    The configuration should provide the following parameters;
    - Host name and port of the BucketFS service (EXTERNAL_HOST_NAME, BUCKETFS_PORT),
    - Client security credentials (BUCKETFS_USER, BUCKETFS_PASSWORD).
    - Bucket name (BUCKETFS_BUCKET)
    Optional parameters include:
    - Secured comm flag (ENCRYPTION), defaults to False.
    Currently, it's not possible to set any of the TLS/SSL parameters. If secured comm
    is selected it automatically sets the certificate validation on.
    """

    # Set up the connection parameters.
    # For now, just use the http. Once the exasol.bucketfs is capable of using the
    # https without validating the server certificate choose between the http and
    # https depending on the ENCRYPTION setting like in the code below:
    # buckfs_url_prefix = "https" if _optional_encryption(conf) else "http"
    buckfs_url_prefix = "http"
    buckfs_url = f"{buckfs_url_prefix}://{conf.EXTERNAL_HOST_NAME}:{conf.BUCKETFS_PORT}"
    buckfs_credentials = {
        conf.BUCKETFS_BUCKET: {
            "username": conf.BUCKETFS_USER,
            "password": conf.BUCKETFS_PASSWORD,
        }
    }

    # Connect to the BucketFS service and navigate to the bucket of choice.
    bucketfs = bfs.Service(buckfs_url, buckfs_credentials)
    return bucketfs[conf.BUCKETFS_BUCKET]
