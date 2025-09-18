from pathlib import Path

from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import SCS_OPTIONS
from exasol.nb_connector.cli.util import add_options


@cli.group(
    help="""Check the configuration current contained in the Secure
    Configuration Storage."""
)
def check():
    pass


@check.command(
    help="""Verify if all required parameters are saved in the SCS."""
)
@add_options(SCS_OPTIONS)
def configuration(scs_file: Path, scs_password: str):
    # conf = None
    # b = get_backend(conf)
    pass


@check.command(
    help="""Verify successful connection to the configured Exasol database
    instance."""
)
@add_options(SCS_OPTIONS)
def connection(scs_file: Path, scs_password: str):
    print(f'scs_file: {scs_file}')
    print(f'scs_password: {scs_password}')
