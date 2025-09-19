import click

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.cli.scs_options import ScsOption

ONPREM_DB_OPTIONS = [
    ScsOption(
        "--db-host-name",
        metavar="HOST",
        type=str,
        default="localhost",
        show_default=True,
        help="Database connection host name",
        scs_key=CKey.db_host_name,
    ),
    ScsOption(
        "--db-port",
        metavar="PORT",
        type=int,
        default=8563,
        show_default=True,
        help="Database connection port",
        scs_key=CKey.db_port,
    ),
    ScsOption(
        "--db-username",
        metavar="USERNAME",
        type=str,
        help="Database user name",
        scs_key=CKey.db_user,
    ),
    ScsOption(
        "--db-password",
        metavar="PASSWORD",
        type=str,
        prompt=True,
        prompt_required=False,
        hide_input=True,
        envvar="EXASOL_DB_PASSWORD",
        show_envvar=True,
        help="Database password",
        scs_key=CKey.db_password,
    ),
    ScsOption(
        "--db-use-encryption/--no-db-use-encryption",
        type=bool,
        default=True,
        show_default=True,
        help="Whether to encrypt communication with the database or not",
        scs_key=CKey.db_encryption,
    ),
]
