import click
from exasol.nb_connector.ai_lab_config import Accelerator

from exasol.ai.mcp.server.cli._decorators import add_options
from exasol.ai.mcp.server.cli.groups import cli
from exasol.ai.mcp.server.cli.options import (
    BUCKETFS_OPTIONS,
    COMMON_OPTIONS,
    DOCKER_DB_OPTIONS,
    ONPREM_OPTIONS,
    SAAS_OPTIONS,
    SSL_OPTIONS,
)


@cli.group()
def configure():
    pass


@configure.command("onprem")
@add_options(ONPREM_OPTIONS)
@add_options(BUCKETFS_OPTIONS)
@add_options(SSL_OPTIONS)
@add_options(COMMON_OPTIONS)
def configure_onprem(
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
    bucketfs_service_name: str,
    bucketfs_bucket_name: str,
    bucketfs_use_encryption: bool,
    ssl_use_cert_validation: bool,
    ssl_cert_path: str,
    db_schema: str,
):
    print(f'Password is {db_password}')


@configure.command("saas")
@add_options(SAAS_OPTIONS)
@add_options(SSL_OPTIONS)
@add_options(COMMON_OPTIONS)
def configure_saas(
    saas_url: str,
    saas_account_id: str,
    saas_database_id: str,
    saas_database_name: str,
    saas_token: str,
    ssl_use_cert_validation: bool,
    ssl_cert_path: str,
    db_schema: str,
):
    pass


@configure.command("docker-db")
@add_options(DOCKER_DB_OPTIONS)
@add_options(COMMON_OPTIONS)
def configure_docker_db(
    docker_db_mem_size: int,
    docker_db_disk_size: int,
    docker_db_accelerator: Accelerator,
    db_schema: str,
):
    pass

