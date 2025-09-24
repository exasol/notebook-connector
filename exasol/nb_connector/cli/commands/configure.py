from pathlib import Path

from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import (
    DOCKER_DB_OPTIONS,
    ONPREM_OPTIONS,
    SAAS_OPTIONS,
)
from exasol.nb_connector.cli.param_wrappers import add_params


@cli.group()
def configure():
    """
    Add configuration options to the Secure Configuration Storage.
    """
    pass


@configure.command("onprem")
@add_params(ONPREM_OPTIONS)
def configure_onprem(scs_file: Path, **kwargs):
    """
    Configure connection to an Exasol on-premise instance.
    """
    pass


@configure.command("saas")
@add_params(SAAS_OPTIONS)
def configure_saas(scs_file: Path, **kwargs):
    """
    Configure connection to an Exasol SaaS instance.

    Configuring one of the parameters --saas-database-id and
    --saas-database-name is sufficient.
    """
    pass


@configure.command("docker-db")
@add_params(DOCKER_DB_OPTIONS)
def configure_docker_db(scs_file: Path, **kwargs):
    """
    Configure connection to an Exasol Docker instance.
    """
    pass
