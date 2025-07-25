from pathlib import Path

import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slct_manager import (
    DEFAULT_SLC_SESSION,
    FLAVORS_PATH_IN_SLC_REPO,
    SlcSession,
    SlctManager,
    SlctManagerMissingScsEntry,
)

CUDA_FLAVOR = "cuda-flavor-1.0"
NON_CUDA_FLAVOR = "non-cuda-flavor-2.2"


@pytest.fixture
def slc_secrets(secrets) -> Secrets:
    secrets.save(CKey.slc_target_dir, "slc/target/dir")
    return secrets


@pytest.fixture
def populated_secrets(slc_secrets) -> Secrets:
    SlcSession("CUDA").save_flavor(slc_secrets, CUDA_FLAVOR)
    SlcSession("NON_CUDA").save_flavor(slc_secrets, NON_CUDA_FLAVOR)
    return slc_secrets


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


def test_undefined_flavor(slc_secrets: Secrets):
    """
    secrets does not contain the key SlcSession.CUDA.  Tests expects
    SlctManager to raise an SlcFlavorNotFoundError
    """
    with pytest.raises(
        SlctManagerMissingScsEntry, match="does not contain an SLC flavor"
    ):
        SlctManager(slc_secrets, slc_session="CUDA")


def test_default_flavor(slc_secrets: Secrets):
    """
    secrets does not contain any key.  The test case still expects
    the SlctManager to return the default flavor for the default session.
    """
    testee = SlctManager(slc_secrets, slc_session=SlcSession.DEFAULT)
    assert testee.flavor_name == SlcSession.DEFAULT_FLAVOR


def test_save_flavor(slc_secrets):
    DEFAULT_SLC_SESSION.save_flavor(slc_secrets, "abc")
    testee = SlctManager(slc_secrets)
    assert testee.flavor_name == "abc"
