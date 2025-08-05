import re
from pathlib import Path

import pytest

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slct_manager import (
    DEFAULT_SLC_SESSION,
    FLAVORS_PATH_IN_SLC_REPO,
    # SlcSession,
    ScriptLanguageContainer,
    SlcSessionError,
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
    "session_name, expected_flavor",
    [
        ("CUDA", CUDA_FLAVOR),
        ("NON_CUDA", NON_CUDA_FLAVOR),
    ],
)
def test_existing_flavor(
    populated_secrets: Secrets,
    session_name: str,
    expected_flavor: str,
):
    slc_session = SlcSession(session_name)
    testee = ScriptLanguageContainer(populated_secrets, slc_session=slc_session)
    expected = FLAVORS_PATH_IN_SLC_REPO / expected_flavor
    assert testee.flavor_path == str(expected)


def test_undefined_flavor(slc_secrets: Secrets):
    """
    secrets does not contain the key for SLC session "CUDA".  The test
    expects ScriptLanguageContainer to raise an SlcSessionError.
    """
    with pytest.raises(
        SlcSessionError, match="does not contain an SLC flavor"
    ):
        ScriptLanguageContainer(slc_secrets, slc_session=SlcSession("CUDA"))


def test_default_flavor(slc_secrets: Secrets, caplog):
    """
    secrets does not contain the key for any SLC flavor.  The test still
    expects the ScriptLanguageContainer to return the default flavor for the default
    session.
    """
    testee = ScriptLanguageContainer(slc_secrets)
    assert testee.flavor_name == SlcSession.DEFAULT_FLAVOR
    assert re.match("WARNING .* Using default flavor", caplog.text)


@pytest.mark.parametrize("name", ["", None])
def test_empty_session_name(name):
    """
    Verify empty string or None are not accepted as name of a session.
    """
    with pytest.raises(RuntimeError):
        SlcSession(name=name)


def test_save_flavor(slc_secrets):
    DEFAULT_SLC_SESSION.save_flavor(slc_secrets, "abc")
    testee = ScriptLanguageContainer(slc_secrets)
    assert testee.flavor_name == "abc"
