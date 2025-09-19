import click

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.cli.scs_options import ScsOption

EXTRA_SAAS_OPTIONS = [
    ScsOption(
        "--saas-url",
        metavar="URL",
        type=str,
        default="https://cloud.exasol.com",
        show_default=True,
        help="SaaS service URL",
        scs_key=CKey.saas_url,
    ),
    ScsOption(
        "--saas-account-id",
        metavar="ACCOUNT_ID",
        type=str,
        help="SaaS account ID",
        scs_key=CKey.saas_account_id,
    ),
    ScsOption(
        "--saas-database-id",
        metavar="ID",
        type=str,
        help="SaaS database ID",
        scs_key=CKey.saas_database_id,
        scs_alternative_key=CKey.saas_database_name,
    ),
    ScsOption(
        "--saas-database-name",
        metavar="NAME",
        type=str,
        help="SaaS database name",
        scs_key=CKey.saas_database_name,
        scs_alternative_key=CKey.saas_database_id,
    ),
    ScsOption(
        "--saas-token",
        metavar="PAT",
        type=str,
        prompt=True,
        prompt_required=False,
        hide_input=True,
        envvar="EXASOL_SAAS_TOKEN",
        show_envvar=True,
        help="SaaS personal access token",
        scs_key=CKey.saas_token,
    ),
]
