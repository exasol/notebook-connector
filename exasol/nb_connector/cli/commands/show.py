from pathlib import Path

from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import SCS_OPTIONS
from exasol.nb_connector.cli.util import add_options


@cli.command(
    help="""Show the configuration currently saved to the Secure Configuration
    Storage."""
)
@add_options(SCS_OPTIONS)
def show(
    scs_file: Path,
    scs_password: str,
):
    pass
