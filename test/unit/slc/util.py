import contextlib
from collections.abc import Iterator
from pathlib import Path

import pytest

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.slc_session import SlcSession


class SecretsMock(Secrets):
    def __init__(
        self,
        session: str,
        initial: dict[str, str],
    ):
        self.session = session
        self._mock = initial

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
        def slc_options() -> Iterator[list[tuple[str, str]]]:
            for key, value in [
                ("FLAVOR", flavor),
                ("LANGUAGE_ALIAS", language_alias),
                ("DIR", checkout_dir),
            ]:
                if value:
                    yield f"SLC_{key}_{session}", str(value)

        return cls(session, dict(slc_options()))


SESSION_ARGS = {
    "checkout_dir": "checkout directory",
    "flavor": "flavor",
    "language_alias": "language alias",
}


def secrets_without(session: str, argument: str):
    args = dict(SESSION_ARGS)
    args[argument] = None
    return SecretsMock.for_slc(session, **args)


@contextlib.contextmanager
def not_raises(exception):
    try:
        yield
    except exception:
        raise pytest.fail(f"DID RAISE {exception}")
