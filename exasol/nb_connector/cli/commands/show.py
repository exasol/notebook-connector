from pathlib import Path

from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import SCS_OPTIONS
from exasol.nb_connector.cli.param_wrappers import add_params


@cli.command()
@add_params(SCS_OPTIONS)
def show(scs_file: Path):
    """
    Show the configuration currently saved to the Secure Configuration
    Storage.
    """
    pass
