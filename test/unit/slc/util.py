from __future__ import annotations

import contextlib
from test.utils.secrets import SecretsMock

import pytest
from exasol.slc.models.compression_strategy import CompressionStrategy

from exasol.nb_connector.slc.slc_compression_strategy import SlcCompressionStrategy
from exasol.nb_connector.slc.slc_flavor import SlcFlavor


class SlcSecretsMock(SecretsMock):
    def __init__(self, slc_name: str):
        super().__init__()
        self.slc_name = slc_name

    @classmethod
    def create(
        cls,
        slc_name: str,
        flavor: str | None = "Vanilla",
        compression_strategy: CompressionStrategy = CompressionStrategy.NONE,
    ) -> SlcSecretsMock:
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
