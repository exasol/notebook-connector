import ipywidgets as widgets

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.config.generic import get_config

DEFAULT_SCHEMA = "Default Schema"


def get_onprem(conf: Secrets) -> widgets.Widget:
    """
    Creates a UI form for editing an external Exasol Database configuration.
    """

    inputs = [
        [
            (
                "Host Name",
                widgets.Text(value=conf.get(CKey.db_host_name, "localhost")),
                CKey.db_host_name,
            ),
            (
                "Port",
                widgets.IntText(value=int(conf.get(CKey.db_port) or 8563)),
                CKey.db_port,
            ),
            ("User Name", widgets.Text(value=conf.get(CKey.db_user)), CKey.db_user),
            (
                "Password",
                widgets.Password(value=conf.get(CKey.db_password)),
                CKey.db_password,
            ),
            (
                DEFAULT_SCHEMA,
                widgets.Text(value=conf.get(CKey.db_schema, "AI_LAB")),
                CKey.db_schema,
            ),
            (
                "Encrypted Comm.",
                widgets.Checkbox(
                    value=conf.get(CKey.db_encryption, "True") == "True", indent=False
                ),
                CKey.db_encryption,
            ),
        ],
        [
            (
                "External Host Name",
                widgets.Text(value=conf.get(CKey.bfs_host_name, "localhost")),
                CKey.bfs_host_name,
            ),
            (
                "Internal Host Name",
                widgets.Text(value=conf.get(CKey.bfs_host_name, "localhost")),
                CKey.bfs_internal_host_name,
            ),
            (
                "External Port",
                widgets.IntText(value=int(conf.get(CKey.bfs_port) or 2580)),
                CKey.bfs_port,
            ),
            (
                "Internal Port",
                widgets.IntText(value=int(conf.get(CKey.bfs_port) or 2580)),
                CKey.bfs_internal_port,
            ),
            ("User Name", widgets.Text(value=conf.get(CKey.bfs_user)), CKey.bfs_user),
            (
                "Password",
                widgets.Password(value=conf.get(CKey.bfs_password)),
                CKey.bfs_password,
            ),
            (
                "Service Name",
                widgets.Text(value=conf.get(CKey.bfs_service, "bfsdefault")),
                CKey.bfs_service,
            ),
            (
                "Bucket Name",
                widgets.Text(value=conf.get(CKey.bfs_bucket, "default")),
                CKey.bfs_bucket,
            ),
            (
                "Encrypted Comm.",
                widgets.Checkbox(
                    value=conf.get(CKey.bfs_encryption, "True") == "True", indent=False
                ),
                CKey.bfs_encryption,
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
            (
                "Certificate File",
                widgets.Text(value=conf.get(CKey.client_cert)),
                CKey.client_cert,
            ),
            (
                "Private Key File",
                widgets.Text(value=conf.get(CKey.client_key)),
                CKey.client_key,
            ),
        ],
    ]

    group_names = [
        "Database Connection",
        "BucketFS Connection",
        "TLS/SSL Configuration",
    ]

    return get_config(conf, inputs, group_names)
