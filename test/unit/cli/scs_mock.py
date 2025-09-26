import types
from unittest.mock import Mock

from _pytest.monkeypatch import MonkeyPatch

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.cli.processing import option_mapper


class ScsMock:
    """
    Instead of using a real Secure Configuration Storage, this mock
    simpulates it using a simple dict().
    """

    def __init__(
        self,
        backend: StorageBackend | None = None,
        use_itde: bool | None = None,
    ):
        self._dict = dict()
        if backend:
            self.save(CKey.storage_backend, backend.name)
        if use_itde is not None:
            self.save(CKey.use_itde, str(use_itde))

    def save(self, key: CKey, value: str) -> None:
        self._dict[key.name] = str(value)

    def get(self, key: CKey, default: str | None = None) -> str | None:
        return self._dict.get(key.name, default)


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
        self._monkeypatch.setattr(option_mapper.report, func, Mock())

    def patch(
        self,
        backend: StorageBackend | None = None,
        use_itde: bool | None = None,
    ) -> ScsMock():
        scs_mock = ScsMock(backend, use_itde)
        getter = Mock(return_value=scs_mock)
        self._monkeypatch.setattr(self._module, "get_scs", getter)
        return scs_mock
