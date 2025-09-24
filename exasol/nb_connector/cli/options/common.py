from pathlib import Path

import click

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.cli.param_wrappers import (
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

SAVE_OPTIONS = [
    ScsOption(
        "--overwrite-backend/--no-overwrite-backend",
        is_flag=True,
        help="Whether to overwrite a different backend in the SCS.",
    )
]

COMMON_OPTIONS = [
    ScsOption(
        "--db-schema",
        metavar="DB_SCHEMA",
        type=str,
        help="Database schema for installing UDFs of Exasol extensions",
        scs_key=CKey.db_schema,
    )
]
