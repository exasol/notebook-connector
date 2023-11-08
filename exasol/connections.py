import pyexasol
from sqlalchemy import create_engine
from exasol.bucketfs import Service, Bucket
from secret_store import Secrets


def get_external_host(conf: Secrets):
    """Constructs the host part of a DB URL using provided configuration parameters."""

    return f'{conf.EXTERNAL_HOST_NAME}:{conf.HOST_PORT}'


def open_pyexasol_connection(conf: Secrets, compression: bool = True) -> pyexasol.ExaConnection:
    """Opens a pyexasol connection using provided configuration parameters."""

    dsn = get_external_host(conf)
    return pyexasol.connect(dsn=dsn, user=conf.USER, password=conf.PASSWORD, compression=compression)


def open_sqlalchemy_connection(conf: Secrets, ssl_certificate: str = 'SSL_VERIFY_NONE'):
    """
    Creates an Exasol SQLAlchemy engine using provided configuration parameters
    and an optional TLS/SSL certificate.
    """

    websocket_url = f'exa+websocket://{conf.USER}:{conf.PASSWORD}' \
                    f'@{get_external_host(conf)}/{conf.SCHEMA}?SSLCertificate={ssl_certificate}'
    return create_engine(websocket_url)


def open_bucketfs_connection(conf: Secrets) -> Bucket:
    """
    Connects to the BucketFS service using provided configuration parameters.
    Returns the Bucket object for the bucket selected in the configuration.
    """

    # Setup the connection parameters.
    buckfs_url_prefix = 'https' if conf.BUCKETFS_USE_HTTPS == 'True' else 'http'
    buckfs_url = f'{buckfs_url_prefix}://{conf.EXTERNAL_HOST_NAME}:{conf.BUCKETFS_PORT}'
    buckfs_credentials = {conf.BUCKETFS_BUCKET: {'username': conf.BUCKETFS_USER, 'password': conf.BUCKETFS_PASSWORD}}

    # Connect to the BucketFS service and navigate to the bucket of choice.
    bucketfs = Service(buckfs_url, buckfs_credentials)
    return bucketfs[conf.BUCKETFS_BUCKET]
