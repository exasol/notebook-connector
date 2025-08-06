from unittest.mock import Mock

from exasol.nb_connector.secret_store import Secrets


class SecretsMock(Secrets):
    def __init__(
        self,
        session: str,
        initial: dict[str, str] | None = None,
    ):
        self.session = session
        if initial:
            self._mock = {f"{prefix}_{session}": v for prefix, v in initial.items()}
        else:
            self._mock = {}

    def get(self, key: str) -> str:
        return self._mock.get(key)

    def __getitem__(self, key: str) -> str:
        val = self._mock.get(key)
        if val is None:
            raise AttributeError(f'Unknown key "{key}"')
        return val

    def save(self, key: str, value: str) -> "Secrets":
        self._mock[key] = value
        return self


SESSION_ATTS = {
    "SLC_FLAVOR": "SLC flavor",
    "SLC_LANGUAGE_ALIAS": "SLC language alias",
    "SLC_DIR": "SLC working directory",
}


def secrets_without(session: str, key_prefix: str):
    atts = dict(SESSION_ATTS)
    atts.pop(key_prefix, None)
    return SecretsMock(session, atts)
