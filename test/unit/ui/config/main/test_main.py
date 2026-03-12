from unittest.mock import MagicMock

from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.ui.config import main


def _assert_configure_db(monkeypatch, backend, conf_get_value, target_attr):
    """Run configure_db and assert it returns the result object."""
    result = object()
    conf = MagicMock()
    if conf_get_value:
        conf.get.return_value = conf_get_value

    monkeypatch.setattr(main, "get_backend", lambda _: backend)
    monkeypatch.setattr(main, target_attr, lambda _: result)

    assert main.configure_db(conf) is result


def test_configure_db_saas(monkeypatch):
    """Use SaaS configuration when backend is SaaS."""
    _assert_configure_db(monkeypatch, StorageBackend.saas, None, "get_saas")


def test_configure_db_docker_db(monkeypatch):
    """Use Docker DB when on-prem backend and flag is True."""
    _assert_configure_db(
        monkeypatch, StorageBackend.onprem, "True", "docker_db_configuration"
    )


def test_configure_db_onprem(monkeypatch):
    """Use on-prem configuration when on-prem backend and flag is False."""
    _assert_configure_db(monkeypatch, StorageBackend.onprem, "False", "get_onprem")
