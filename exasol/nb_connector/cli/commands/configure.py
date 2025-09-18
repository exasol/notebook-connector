import click
from pathlib import Path
from exasol.nb_connector.ai_lab_config import Accelerator, StorageBackend

from exasol.nb_connector.cli.util import add_options
from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import (
    BUCKETFS_OPTIONS,
    COMMON_CONFIGURE_OPTIONS,
    DOCKER_DB_OPTIONS,
    ONPREM_OPTIONS,
    SAAS_OPTIONS,
    SCS_OPTIONS,
    SSL_OPTIONS,
)


@cli.group(
    help="Add configuration options to the Secure Configuration Storage."
)
def configure():
    pass


@configure.command(
    "onprem",
    help="Configure connection to an Exasol on-premise instance."
)
@add_options(SCS_OPTIONS)
@add_options(ONPREM_OPTIONS)
@add_options(BUCKETFS_OPTIONS)
@add_options(SSL_OPTIONS)
@add_options(COMMON_CONFIGURE_OPTIONS)
def configure_onprem(
    scs_file: Path,
    scs_password: str,
    db_host_name: str,
    db_port: int,
    db_username: str,
    db_password: str,
    db_use_encryption: bool,
    bucketfs_host: str,
    bucketfs_host_internal: str,
    bucketfs_port: int,
    bucketfs_port_internal: int,
    bucketfs_username: str,
    bucketfs_password: str,
    bucketfs_name: str,
    bucket: str,
    bucketfs_use_encryption: bool,
    ssl_use_cert_validation: bool,
    ssl_cert_path: Path,
    db_schema: str,
):
    backend = StorageBackend.onprem
    print(f'SCS Master Password: {scs_password}')
    print(f'DB Password: {db_password}')


@configure.command(
    "saas",
    help="Configure connection to an Exasol SaaS instance."
)
@add_options(SCS_OPTIONS)
@add_options(SAAS_OPTIONS)
@add_options(SSL_OPTIONS)
@add_options(COMMON_CONFIGURE_OPTIONS)
def configure_saas(
    scs_file: Path,
    scs_password: str,
    saas_url: str,
    saas_account_id: str,
    saas_database_id: str,
    saas_database_name: str,
    saas_token: str,
    ssl_use_cert_validation: bool,
    ssl_cert_path: Path,
    db_schema: str,
):
    backend = StorageBackend.saas


@configure.command(
    "docker-db",
    help="Configure connection to an Exasol Docker instance."
)
@add_options(SCS_OPTIONS)
@add_options(DOCKER_DB_OPTIONS)
@add_options(COMMON_CONFIGURE_OPTIONS)
def configure_docker_db(
    scs_file: Path,
    scs_password: str,
    docker_db_mem_size: int,
    docker_db_disk_size: int,
    docker_db_accelerator: Accelerator,
    db_schema: str,
):
    # CKey.use_itde
    # CKey.storage_backend
    backend = StorageBackend.onprem
