import os
from pathlib import Path
from test.unit.cli.scs_mock import ScsPatcher

import pytest

from exasol.nb_connector.ai_lab_config import Accelerator
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.cli.processing import processing
from exasol.nb_connector.cli.processing.backend_selector import BackendSelector
from exasol.nb_connector.connections import get_backend
from exasol.nb_connector.secret_store import Secrets


@pytest.fixture
def scs_patcher(monkeypatch):
    return ScsPatcher(monkeypatch, module=processing)


def _save_only_default_values(scs: Secrets):
    selector = BackendSelector(scs)
    processing.save(
        scs_file=Path("/fictional/scs"),
        backend=selector.backend,
        use_itde=selector.use_itde,
        values={},
    )


def test_save_overwrite_with_warning(scs_patcher, capsys):
    scs_mock = scs_patcher.patch(StorageBackend.saas, use_itde=False)
    processing.save(
        scs_file=Path("/fictional/scs"),
        backend=StorageBackend.onprem,
        use_itde=True,
        values={},
    )
    assert get_backend(scs_mock) == StorageBackend.onprem
    assert scs_mock.get(CKey.use_itde) == "True"
    assert "Warning: Overwriting" in capsys.readouterr().out


def test_save_default(scs_patcher):
    scs_mock = scs_patcher.patch(StorageBackend.onprem, use_itde=False)
    _save_only_default_values(scs_mock)
    assert scs_mock.get(CKey.cert_vld) == "True"


def test_defaults_dont_overwrite_user_values(scs_patcher):
    """
    See https://github.com/exasol/notebook-connector/issues/285
    """
    scs_mock = scs_patcher.patch(StorageBackend.onprem, use_itde=False)
    scs_mock.save(CKey.cert_vld, "False")
    _save_only_default_values(scs_mock)
    assert scs_mock.get(CKey.cert_vld) == "False"


def test_change_value(scs_patcher):
    def save_saas_url(url: str) -> str:
        processing.save(
            scs_file=Path("/fictional/scs"),
            backend=StorageBackend.saas,
            use_itde=False,
            values={"saas_url": url},
        )
        return url

    scs_mock = scs_patcher.patch()
    save_saas_url("H1") == scs_mock.get(CKey.saas_url)
    save_saas_url("H2") == scs_mock.get(CKey.saas_url)


def test_save_enum_value(scs_patcher):
    scs_mock = scs_patcher.patch()
    actual = processing.save(
        scs_file=Path("/fictional/scs"),
        backend=StorageBackend.onprem,
        use_itde=True,
        values={"accelerator": Accelerator.nvidia},
    )
    assert scs_mock.get(CKey.accelerator) == Accelerator.nvidia.name


def test_save_secret_option(scs_patcher, monkeypatch, capsys):
    scs_mock = scs_patcher.patch()
    monkeypatch.setitem(os.environ, "SCS_EXASOL_SAAS_TOKEN", "patty-pat")
    actual = processing.save(
        scs_file=Path("/fictional/scs"),
        backend=StorageBackend.saas,
        use_itde=False,
        values={"saas_token": True},
    )
    assert scs_mock.get(CKey.saas_token) == "patty-pat"
    assert (
        "Reading --saas-token from environment variable SCS_EXASOL_SAAS_TOKEN."
    ) in capsys.readouterr().out
