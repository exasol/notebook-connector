import ipywidgets as widgets
import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ui.transformers.util import te_init


@pytest.fixture
def fake_get_config():
    captured = {}

    def _fake_get_config(conf, inputs, group_names):
        captured["conf"] = conf
        captured["inputs"] = inputs
        captured["group_names"] = group_names
        return "ui"

    return _fake_get_config, captured


def test_get_hf_config_builds_expected_inputs(monkeypatch, secrets, fake_get_config):
    """
    This test checks that the expected inputs are built.
        - It mocks the get_config function to capture the inputs passed to it.
        - It calls get_hf_config and verifies that the captured inputs match the expected values.
        - It also checks that the token value is correctly retrieved from the secrets and passed to the widget.
        - This test ensures that the get_hf_config function correctly builds the UI inputs based on the secrets and configuration.
    """
    secrets.save(CKey.huggingface_token, "hf_token_123")

    fake_config, captured = fake_get_config
    monkeypatch.setattr(te_init, "ai_lab_config", secrets, raising=False)
    monkeypatch.setattr(te_init.generic, "get_config", fake_config)

    result = te_init.get_hf_config(secrets)

    assert result == "ui"
    assert captured["conf"] is secrets
    assert captured["group_names"] == ["Hugging Face Access Parameters"]

    label, widget, key = captured["inputs"][0][0]
    assert label == "Access token"
    assert isinstance(widget, widgets.Password)
    assert widget.value == "hf_token_123"
    assert key == CKey.huggingface_token
