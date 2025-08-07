from pathlib import Path
from unittest.mock import Mock

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.slc_session import SlcSession


class SecretsMock(Secrets):
    def __init__(
        self,
        session: str,
        initial: dict[str, str] | None = None,
    ):
        self.session = session
        self._mock = initial or {}
        # if initial:
        #     self._mock = {f"{prefix}_{session}": v for prefix, v in initial.items()}
        # else:
        #     self._mock = {}

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

    def simulate_checkout(self):
        SlcSession(self, self.session).flavor_dir.mkdir(parents=True)
        return self

    @classmethod
    def for_slc(
        cls,
        session: str,
        checkout_dir: Path | None,
        flavor: str | None = "Vanilla",
        language_alias: str | None = "Spanish",
    ):
        slc_options = {
            "FLAVOR": flavor,
            "LANGUAGE_ALIAS": language_alias,
            "DIR": str(checkout_dir),
        }
        return cls(session, {f"SLC_{k}_{session}": v for k.v in slc_options.items()})


SESSION_ATTS = {
    "SLC_FLAVOR": "SLC flavor",
    "SLC_LANGUAGE_ALIAS": "SLC language alias",
    "SLC_DIR": "SLC working directory",
}


def secrets_without(session: str, key_prefix: str):
    atts = dict(SESSION_ATTS)
    atts.pop(key_prefix, None)
    return SecretsMock(session, atts)
