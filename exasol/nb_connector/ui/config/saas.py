import ipywidgets as widgets

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.config.generic import generic_configuration

DEFAULT_SCHEMA = "Default Schema"


def get_saas(conf: Secrets) -> widgets.Widget:
    """
    Creates a UI form for editing the Exasol SaaS database configuration.
    """

    inputs = [
        [
            (
                "Service URL",
                widgets.Text(value=conf.get(CKey.saas_url, "https://cloud.exasol.com")),
                CKey.saas_url,
            ),
            (
                "Account ID",
                widgets.Password(value=conf.get(CKey.saas_account_id)),
                CKey.saas_account_id,
            ),
            (
                "Database ID",
                widgets.Text(value=conf.get(CKey.saas_database_id)),
                CKey.saas_database_id,
            ),
            (
                "Database Name",
                widgets.Text(value=conf.get(CKey.saas_database_name)),
                CKey.saas_database_name,
            ),
            (
                "Personal Access Token",
                widgets.Password(value=conf.get(CKey.saas_token)),
                CKey.saas_token,
            ),
            (
                "Default Schema",
                widgets.Text(value=conf.get(CKey.db_schema, "AI_LAB")),
                CKey.db_schema,
            ),
        ],
        [
            (
                "Validate Certificate",
                widgets.Checkbox(
                    value=conf.get(CKey.cert_vld, "True") == "True", indent=False
                ),
                CKey.cert_vld,
            ),
            (
                "Trusted CA File/Dir",
                widgets.Text(value=conf.get(CKey.trusted_ca)),
                CKey.trusted_ca,
            ),
        ],
    ]

    group_names = ["SaaS DB Configuration", "TLS/SSL Configuration"]

    return generic_configuration(conf, inputs, group_names)
