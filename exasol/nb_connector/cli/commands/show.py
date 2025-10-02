import sys
from pathlib import Path

from exasol.nb_connector.cli import reporting as report
from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import SCS_OPTIONS
from exasol.nb_connector.cli.param_wrappers import add_params
from exasol.nb_connector.cli.processing import processing
from exasol.nb_connector.cli.processing.option_set import ScsCliError


@cli.command()
@add_params(SCS_OPTIONS)
def show(scs_file: Path):
    """
    Show the configuration currently saved to the Secure Configuration
    Storage.
    """
    try:
        processing.show_scs_content(scs_file)
    except ScsCliError as ex:
        report.error(ex)
        sys.exit(1)
