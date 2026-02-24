import pytest
from exasol.slc.models.compression_strategy import CompressionStrategy


@pytest.fixture(scope="session")
def compression_strategy(request) -> CompressionStrategy:
    val = request.config.getoption("--compression-strategy")
    return CompressionStrategy(val)
