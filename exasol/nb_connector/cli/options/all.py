import click
from pathlib import Path


SCS_OPTIONS = [
    click.option(
        "--scs-file",
        metavar="PATH",
        type=Path,
        help="File containing the Secure Configuration Storage (SCS)",
    ),
    click.option(
        "--scs-master-password",
        "scs_password",
        metavar="PASSWORD",
        type=str,
        prompt=True,
        prompt_required=False,
        # show_envvar=True,
        hide_input=True,
        envvar="SCS_MASTER_PASSWORD",
        show_envvar=True,
        help="Master password for the SCS",
    ),
]


COMMON_CONFIGURE_OPTIONS = [
    click.option(
        "--db-schema",
        metavar="DB_SCHEMA",
        type=str,
        help="Database schema for installing UDFs of Exasol extensions",
    )
]
