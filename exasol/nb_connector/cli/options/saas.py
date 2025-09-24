from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.cli.param_wrappers import (
    ScsOption,
    ScsSecretOption,
)

EXTRA_SAAS_OPTIONS = [
    ScsOption(
        "--saas-url",
        metavar="URL",
        type=str,
        default="https://cloud.exasol.com",
        help="Exasol SaaS service URL",
        scs_key=CKey.saas_url,
    ),
    ScsOption(
        "--saas-account-id",
        metavar="ACCOUNT_ID",
        type=str,
        help="Exasol SaaS account ID",
        scs_key=CKey.saas_account_id,
    ),
    # CKey.saas_database_id and CKey.saas_database_name can be used
    # alternatively, see
    # https://github.com/exasol/saas-api-python/blob/main/exasol/saas/client/api_access.py#L134
    ScsOption(
        "--saas-database-id",
        metavar="ID",
        type=str,
        help="Exasol SaaS database ID",
        scs_key=CKey.saas_database_id,
        scs_alternative_key=CKey.saas_database_name,
    ),
    ScsOption(
        "--saas-database-name",
        metavar="NAME",
        type=str,
        help="Exasol SaaS database name",
        scs_key=CKey.saas_database_name,
        scs_alternative_key=CKey.saas_database_id,
    ),
    ScsSecretOption(
        "--saas-token",
        envvar="SCS_EXASOL_SAAS_TOKEN",
        prompt="Exasol SaaS personal access token (PAT)",
        scs_key=CKey.saas_token,
        metavar="PAT",
    ),
]
