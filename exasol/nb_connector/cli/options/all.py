from pathlib import Path

import click

from exasol.nb_connector.cli.scs_options import (
    ScsArgument,
    ScsOption,
)

SCS_OPTIONS = [
    ScsArgument(
        "scs_file",
        metavar="SCS_FILE",
        type=Path,
        required=True,
        envvar="SCS_FILE",
    ),
]


COMMON_CONFIGURE_OPTIONS = [
    ScsOption(
        "--db-schema",
        metavar="DB_SCHEMA",
        type=str,
        help="Database schema for installing UDFs of Exasol extensions",
    )
]
