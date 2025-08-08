from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path

import pytest

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.slc_flavor import SlcFlavor


class SecretsMock(Secrets):
    def __init__(
        self,
        slc_name: str,
        # initial: dict[str, str],
    ):
        self.slc_name = slc_name
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

    # def simulate_checkout(self):
    #     SlcSession(self, self.session).flavor_dir.mkdir(parents=True)
    #     return self

    @classmethod
    def for_slc(
        cls,
        slc_name: str,
        flavor: str | None = "Vanilla",
    ) -> SecretsMock:
        instance = cls(slc_name)
        if flavor:
            SlcFlavor(slc_name).save(instance, flavor)
        return instance

    @classmethod
    def old_for_slc(
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
                    yield f"SLC_{key}_{session.upper()}", str(value)

        return cls(session, dict(slc_options()))


SESSION_OPTIONS = {
    "checkout_dir": "checkout directory",
    "flavor": "flavor",
}


def secrets_without(session: str, argument: str):
    args = dict(SESSION_OPTIONS)
    args[argument] = None
    return SecretsMock.for_slc(session, **args)


@contextlib.contextmanager
def not_raises(exception):
    try:
        yield
    except exception:
        raise pytest.fail(f"DID RAISE {exception}")
