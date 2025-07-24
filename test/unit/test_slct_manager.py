import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slct_manager import (
    SlcSession,
    SlctManager,
)

CUDA_FLAVOR = "cuda-flavor-1.0"
NON_CUDA_FLAVOR = "non-cuda-flavor-2.2"


@pytest.fixture
def secrets_with_slc_flavors(secrets) -> Secrets:
    secrets.save(CKey.slc_flavor_cuda, CUDA_FLAVOR)
    secrets.save(CKey.slc_flavor_non_cuda, NON_CUDA_FLAVOR)
    return secrets


@pytest.mark.parametrize ("session, expected_flavor", [
    (SlcSession.CUDA, CUDA_FLAVOR),
    (SlcSession.NON_CUDA, NON_CUDA_FLAVOR),
])
def test_slc_session_to_flavor(
    secrets_with_slc_flavors: Secrets,
    session: SlcSession,
    expected_flavor: str,
):
    key = session.value
    flavor_name = secrets_with_slc_flavors.get(key)
    assert flavor_name == expected_flavor
