from __future__ import annotations

import contextlib

import pytest
from exasol.slc.models.compression_strategy import CompressionStrategy

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.slc_compression_strategy import SlcCompressionStrategy
from exasol.nb_connector.slc.slc_flavor import SlcFlavor


class SecretsMock(Secrets):
    def __init__(
        self,
        slc_name: str,
    ):
        self.slc_name = slc_name
        self._mock: dict[str, str] = {}

    def get(self, key: str | CKey, default_value: str | None = None) -> str | None:
        key = key.name if isinstance(key, CKey) else key
        return self._mock.get(key)

    def __getitem__(self, key: str | CKey) -> str:
        key = key.name if isinstance(key, CKey) else key
        val = self._mock.get(key)
        if val is None:
            raise AttributeError(f'Unknown key "{key}"')
        return val

    def save(self, key: str | CKey, value: str) -> Secrets:
        key = key.name if isinstance(key, CKey) else key
        self._mock[key] = value
        return self

    @classmethod
    def for_slc(
        cls,
        slc_name: str,
        flavor: str | None = "Vanilla",
        compression_strategy: CompressionStrategy = CompressionStrategy.NONE,
    ) -> SecretsMock:
        instance = cls(slc_name)
        if flavor:
            SlcFlavor(slc_name).save(instance, flavor)
            SlcCompressionStrategy(slc_name).save(instance, compression_strategy)
        return instance


@contextlib.contextmanager
def not_raises(exception):
    try:
        yield
    except exception:
        raise pytest.fail(f"DID RAISE {exception}")
