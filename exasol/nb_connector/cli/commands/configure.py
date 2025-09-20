from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import (
    DOCKER_DB_OPTIONS,
    ONPREM_OPTIONS,
    SAAS_OPTIONS,
)
from exasol.nb_connector.cli.scs_options import click_options


@cli.group()
def configure():
    """
    Add configuration options to the Secure Configuration Storage.
    """
    pass


@configure.command("onprem")
@click_options(ONPREM_OPTIONS)
def configure_onprem(**kwargs):
    """
    Configure connection to an Exasol on-premise instance.
    """
    pass


@configure.command("saas")
@click_options(SAAS_OPTIONS)
def configure_saas(**kwargs):
    """
    Configure connection to an Exasol SaaS instance.

    Configuring one of the parameters --saas-database-id and
    --saas-database-name is sufficient.
    """
    pass


@configure.command("docker-db")
@click_options(DOCKER_DB_OPTIONS)
def configure_docker_db(**kwargs):
    """
    Configure connection to an Exasol Docker instance.
    """
    pass
