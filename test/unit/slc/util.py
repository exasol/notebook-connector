from __future__ import annotations

import contextlib

import pytest

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.slc_flavor import SlcFlavor


class SecretsMock(Secrets):
    def __init__(
        self,
        slc_name: str,
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

    def save(self, key: str, value: str) -> Secrets:
        self._mock[key] = value
        return self

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


@contextlib.contextmanager
def not_raises(exception):
    try:
        yield
    except exception:
        raise pytest.fail(f"DID RAISE {exception}")
