from unittest.mock import MagicMock

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ui.config import onprem


def _build_conf_with_values(values):
    """Create a mock config that returns values by key."""
    conf = MagicMock()
    conf.get.side_effect = lambda key, default=None: values.get(key, default)
    return conf


def _capture_generic(monkeypatch, captured):
    """Patch generic_configuration to capture inputs and group names."""
    def fake_generic(conf, inputs, group_names):
        captured["inputs"] = inputs
        captured["group_names"] = group_names
        return "ui"

    monkeypatch.setattr(onprem, "generic_configuration", fake_generic)


def test_get_onprem_builds_expected_inputs(monkeypatch):
    """Ensure on-prem UI inputs are built with expected defaults."""
    captured = {}
    _capture_generic(monkeypatch, captured)

    values = {
        CKey.db_host_name: "db-host",
        CKey.db_port: "1234",
        CKey.db_user: "sys",
        CKey.db_password: "pw",
        CKey.db_schema: "SCHEMA",
        CKey.db_encryption: "False",
        CKey.bfs_host_name: "bfs-host",
        CKey.bfs_port: "2590",
        CKey.bfs_user: "bfs-user",
        CKey.bfs_password: "bfs-pass",
        CKey.bfs_service: "bfsservice",
        CKey.bfs_bucket: "bucket",
        CKey.bfs_encryption: "True",
        CKey.cert_vld: "False",
        CKey.trusted_ca: "/ca.pem",
        CKey.client_cert: "/client.pem",
        CKey.client_key: "/client.key",
    }
    conf = _build_conf_with_values(values)

    assert onprem.get_onprem(conf) == "ui"

    assert captured["group_names"] == [
        "Database Connection",
        "BucketFS Connection",
        "TLS/SSL Configuration",
    ]

    db_inputs, bfs_inputs, tls_inputs = captured["inputs"]

    assert db_inputs[0][1].value == "db-host"
    assert db_inputs[1][1].value == 1234
    assert bfs_inputs[2][1].value == 2590
    assert bfs_inputs[8][1].value is True
    assert tls_inputs[0][1].value is False
    assert tls_inputs[1][1].value == "/ca.pem"
    assert tls_inputs[2][1].value == "/client.pem"
    assert tls_inputs[3][1].value == "/client.key"