from pathlib import Path

from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import SCS_OPTIONS
from exasol.nb_connector.cli.scs_options import click_options


@cli.command()
@click_options(SCS_OPTIONS)
def show(scs_file: Path):
    """
    Show the configuration currently saved to the Secure Configuration
    Storage.
    """
    pass
