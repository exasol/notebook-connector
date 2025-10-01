import sys
from pathlib import Path

from exasol.nb_connector.ai_lab_config import (
    StorageBackend,
)
from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import (
    DOCKER_DB_OPTIONS,
    ONPREM_OPTIONS,
    SAAS_OPTIONS,
)
from exasol.nb_connector.cli.param_wrappers import add_params
from exasol.nb_connector.cli.processing import processing


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
    processing.save(
        scs_file,
        StorageBackend.onprem,
        use_itde=False,
        values=kwargs,
    )


@configure.command("saas")
@add_params(SAAS_OPTIONS)
def configure_saas(scs_file: Path, **kwargs):
    """
    Configure connection to an Exasol SaaS instance.

    Configuring one of the parameters --saas-database-id and
    --saas-database-name is sufficient.
    """
    processing.save(
        scs_file,
        StorageBackend.saas,
        use_itde=False,
        values=kwargs,
    )


@configure.command("docker-db")
@add_params(DOCKER_DB_OPTIONS)
def configure_docker_db(scs_file: Path, **kwargs):
    """
    Configure connection to an Exasol Docker instance.
    """
    processing.save(
        scs_file,
        StorageBackend.onprem,
        use_itde=True,
        values=kwargs,
    )
