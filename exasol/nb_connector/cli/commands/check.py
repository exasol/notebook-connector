import sys
from pathlib import Path

import click

from exasol.nb_connector.cli.groups import cli
from exasol.nb_connector.cli.options import SCS_OPTIONS
from exasol.nb_connector.cli.param_wrappers import add_params
from exasol.nb_connector.cli.processing import processing


@cli.command()
@add_params(SCS_OPTIONS)
@click.option(
    "--connect",
    is_flag=True,
    help="""Verify if connecting to the configured Exasol database instance
    succeeds.""",
)
def check(scs_file: Path, connect: bool):
    """
    Check the configuration current contained in the Secure Configuration
    Storage and verify if it contains all required parameters.

    Optionally also verify if a connection to the configured Exasol database
    instance is successful.
    """
    pass
