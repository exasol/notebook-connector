from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.cli.param_wrappers import (
    ScsOption,
    ScsSecretOption,
)

ONPREM_DB_OPTIONS = [
    ScsOption(
        "--db-host-name",
        metavar="HOST",
        type=str,
        help="Database connection host name",
        scs_key=CKey.db_host_name,
    ),
    ScsOption(
        "--db-port",
        metavar="PORT",
        type=int,
        default=8563,
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
    ScsSecretOption(
        "--db-password",
        envvar="SCS_EXASOL_DB_PASSWORD",
        prompt="Exasol database password",
        scs_key=CKey.db_password,
    ),
    ScsOption(
        "--db-use-encryption/--no-db-use-encryption",
        type=bool,
        default=True,
        help="Whether to encrypt communication with the database or not",
        scs_key=CKey.db_encryption,
    ),
]
