import sys
from pathlib import Path

from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import SCS_OPTIONS
from exasol.nb_connector.cli.param_wrappers import add_params
from exasol.nb_connector.cli.processing import processing


@cli.command()
@add_params(SCS_OPTIONS)
def show(scs_file: Path):
    """
    Show the configuration currently saved to the Secure Configuration
    Storage.
    """
    result = processing.show_scs_content(scs_file)
    sys.exit(result)
