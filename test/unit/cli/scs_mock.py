from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend


class ScsMock:
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
