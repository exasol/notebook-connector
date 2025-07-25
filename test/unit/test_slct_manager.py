from pathlib import Path

import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slct_manager import (
    FLAVORS_PATH_IN_SLC_REPO,
    SlctManager,
    SlctManagerMissingScsEntry,
    slc_flavor_key,
)

CUDA_FLAVOR = "cuda-flavor-1.0"
NON_CUDA_FLAVOR = "non-cuda-flavor-2.2"


@pytest.fixture
def populated_secrets(secrets) -> Secrets:
    secrets.save(slc_flavor_key("CUDA"), CUDA_FLAVOR)
    secrets.save(slc_flavor_key("NON_CUDA"), NON_CUDA_FLAVOR)
    secrets.save(CKey.slc_target_dir, "slc/target/dir")
    return secrets


@pytest.mark.parametrize(
    "session, expected_flavor",
    [
        ("CUDA", CUDA_FLAVOR),
        ("NON_CUDA", NON_CUDA_FLAVOR),
    ],
)
def test_existing_flavor(
    populated_secrets: Secrets,
    session: str,
    expected_flavor: str,
):
    testee = SlctManager(populated_secrets, slc_session=session)
    expected = FLAVORS_PATH_IN_SLC_REPO / expected_flavor
    assert testee.flavor_path == str(expected)


def test_undefined_flavor(secrets: Secrets):
    """
    secrets does not contain value for the key SlcSession.CUDA.
    Tests expects SlctManager to raise an SlcFlavorNotFoundError
    """
    with pytest.raises(
        SlctManagerMissingScsEntry, match="does not contain an SLC flavor"
    ):
        SlctManager(secrets, slc_session="CUDA")
