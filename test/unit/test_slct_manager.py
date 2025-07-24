from pathlib import Path

import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slct_manager import (
    SlcSession,
    SlctManager,
    SlctManagerError,
)

CUDA_FLAVOR = "cuda-flavor-1.0"
NON_CUDA_FLAVOR = "non-cuda-flavor-2.2"


@pytest.fixture
def populated_secrets(secrets) -> Secrets:
    secrets.save(CKey.slc_flavor_cuda, CUDA_FLAVOR)
    secrets.save(CKey.slc_flavor_non_cuda, NON_CUDA_FLAVOR)
    secrets.save(CKey.slc_target_dir, "slc/target/dir")
    return secrets


@pytest.mark.parametrize(
    "session, expected_flavor",
    [
        (SlcSession.CUDA, CUDA_FLAVOR),
        (SlcSession.NON_CUDA, NON_CUDA_FLAVOR),
    ],
)
def test_existing_flavor(
    populated_secrets: Secrets,
    session: SlcSession,
    expected_flavor: str,
):
    testee = SlctManager(populated_secrets, slc_session=session)
    # this test is redundant
    # assert testee.slc_dir.flavor_name == expected_flavor
    assert testee.flavor_path == f"flavors/{expected_flavor}"


def test_undefined_flavor(secrets: Secrets):
    """
    secrets does not contain value for the key SlcSession.CUDA.
    Tests expects SlctManager to raise an SlcFlavorNotFoundError
    """
    with pytest.raises(SlctManagerError, match="does not contain an SLC flavor"):
        SlctManager(secrets, SlcSession.CUDA)
