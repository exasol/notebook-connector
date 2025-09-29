import types
from unittest.mock import Mock

from _pytest.monkeypatch import MonkeyPatch

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.cli.processing import option_set


from test.unit.slc.util import SecretsMock


def scs_mock(
    backend: StorageBackend | None = None,
    use_itde: bool | None = None,
    ) -> SecretsMock:
    scs = SecretsMock("some name")
    if backend:
        scs.save(CKey.storage_backend, backend.name)
    if use_itde is not None:
        scs.save(CKey.use_itde, str(use_itde))
    return scs


class ScsPatcher:
    """
    Enables to patch function function get_scs() in the specified module
    and to return an instance of ScsMock() instead, optionally already
    containing a backend selection.
    """

    def __init__(
        self,
        monkeypatch: MonkeyPatch,
        module: types.ModuleType,
    ):
        self._monkeypatch = monkeypatch
        self._module = module

    def disable_reporting(self, func: str):
        self._monkeypatch.setattr(option_set.report, func, Mock())

    def patch(
        self,
        backend: StorageBackend | None = None,
        use_itde: bool | None = None,
    ) -> SecretsMock:
        scs = scs_mock(backend, use_itde)
        getter = Mock(return_value=scs)
        self._monkeypatch.setattr(self._module, "get_scs", getter)
        return scs
