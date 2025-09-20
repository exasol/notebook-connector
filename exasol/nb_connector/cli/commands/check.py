from pathlib import Path

from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import SCS_OPTIONS
from exasol.nb_connector.cli.scs_options import click_options


@cli.group()
def check():
    """
    Check the configuration current contained in the Secure Configuration
    Storage.
    """
    pass


@check.command()
@click_options(SCS_OPTIONS)
def configuration(scs_file: Path):
    """
    Verify if all required parameters are saved in the SCS.
    """
    pass


@check.command()
@click_options(SCS_OPTIONS)
def connection(scs_file: Path):
    """
    Verify successful connection to the configured Exasol database
    instance.
    """
    print(f"scs_file: {scs_file}")
