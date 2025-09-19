from pathlib import Path

from exasol.nb_connector.cli.scs_options import ScsOption

SCS_OPTIONS = [
    ScsOption(
        "--scs-file",
        metavar="FILE",
        type=Path,
        required=True,
        envvar="SCS_FILE",
        show_envvar=True,
        help="File containing the Secure Configuration Storage (SCS)",
    ),
    ScsOption(
        "--scs-master-password",
        "scs_password",
        metavar="PASSWORD",
        type=str,
        required=True,
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
    ScsOption(
        "--db-schema",
        metavar="DB_SCHEMA",
        type=str,
        help="Database schema for installing UDFs of Exasol extensions",
    )
]
