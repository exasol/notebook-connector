from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import (
    DOCKER_DB_OPTIONS,
    ONPREM_OPTIONS,
    SAAS_OPTIONS,
)
from exasol.nb_connector.cli.scs_options import click_options


@cli.group(help="Add configuration options to the Secure Configuration Storage.")
def configure():
    pass


@configure.command(
    "onprem", help="Configure connection to an Exasol on-premise instance."
)
@click_options(ONPREM_OPTIONS)
def configure_onprem(**kwargs):
    pass


@configure.command("saas", help="Configure connection to an Exasol SaaS instance.")
@click_options(SAAS_OPTIONS)
def configure_saas(**kwargs):
    pass


@configure.command(
    "docker-db", help="Configure connection to an Exasol Docker instance."
)
@click_options(DOCKER_DB_OPTIONS)
def configure_docker_db(**kwargs):
    pass
