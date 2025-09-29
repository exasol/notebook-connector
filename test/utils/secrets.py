from __future__ import annotations

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets


def _ensure_str(key: str | CKey) -> str:
    return key.name if isinstance(key, CKey) else key


class SecretsMock(Secrets):
    def __init__(self):
        self._mock: dict[str, str] = {}

    def get(self, key: str | CKey, default_value: str | None = None) -> str | None:
        key = _ensure_str(key)
        return self._mock.get(key)

    def __getitem__(self, key: str | CKey) -> str:
        key = _ensure_str(key)
        val = self._mock.get(key)
        if val is None:
            raise AttributeError(f'Unknown key "{key}"')
        return val

    def save(self, key: str | CKey, value: str) -> Secrets:
        key = _ensure_str(key)
        self._mock[key] = value
        return self

