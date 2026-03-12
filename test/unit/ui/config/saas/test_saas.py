from test.integration.ui.common.utils.ui_utils import mock_conf

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ui.config import saas


def _saas_values():
    """Return fixed SaaS config values for tests."""
    return {
        CKey.saas_url: "https://example.com",
        CKey.saas_account_id: "acct",
        CKey.saas_database_id: "db-id",
        CKey.saas_database_name: "db-name",
        CKey.saas_token: "token",
        CKey.db_schema: "SCHEMA",
        CKey.cert_vld: "False",
        CKey.trusted_ca: "/ca.pem",
    }


def _capture_generic(monkeypatch, captured):
    """Patch generic_configuration to capture inputs and group names."""

    def fake_generic(conf, inputs, group_names):
        captured["conf"] = conf
        captured["inputs"] = inputs
        captured["group_names"] = group_names
        return "ui"

    monkeypatch.setattr(saas, "generic_configuration", fake_generic)


def test_get_saas_builds_expected_inputs(monkeypatch):
    """Ensure SaaS UI inputs are built with expected defaults."""
    captured = {}
    _capture_generic(monkeypatch, captured)

    conf = mock_conf(_saas_values())

    assert saas.get_saas(conf) == "ui"

    inputs = captured["inputs"]
    group_names = captured["group_names"]

    assert group_names == ["SaaS DB Configuration", "TLS/SSL Configuration"]

    db_inputs = inputs[0]
    tls_inputs = inputs[1]

    assert db_inputs[0][0] == "Service URL"
    assert db_inputs[0][1].value == "https://example.com"
    assert db_inputs[1][1].value == "acct"
    assert db_inputs[3][1].value == "db-name"
    assert db_inputs[5][1].value == "SCHEMA"

    assert tls_inputs[0][0] == "Validate Certificate"
    assert tls_inputs[0][1].value is False
    assert tls_inputs[1][1].value == "/ca.pem"
