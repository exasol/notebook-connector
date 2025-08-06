

from pathlib import Path
from test.unit.slc.util import (
    SESSION_ATTS,
    secrets_without,
)
from unittest.mock import Mock

import pytest

# from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
# from exasol.nb_connector.secret_store import Secrets
# from exasol.nb_connector.slc.constants import FLAVORS_PATH_IN_SLC_REPO
from exasol.nb_connector.slc.script_language_container import (
    ScriptLanguageContainer,
    SlcSessionError,
)

# CUDA_FLAVOR = "cuda-flavor-1.0"
# NON_CUDA_FLAVOR = "non-cuda-flavor-2.2"
#
#
# # obsolete
# @pytest.fixture
# def slc_secrets(secrets) -> Secrets:
#     secrets.save(CKey.slc_target_dir, "slc/target/dir")
#     return secrets
#
#
# # obsolete
# @pytest.fixture
# def populated_secrets(slc_secrets) -> Secrets:
#     SlcSession("CUDA").save_flavor(slc_secrets, CUDA_FLAVOR)
#     SlcSession("NON_CUDA").save_flavor(slc_secrets, NON_CUDA_FLAVOR)
#     return slc_secrets
#
#
# @pytest.mark.skip
# @pytest.mark.parametrize(
#     "session_name, expected_flavor",
#     [
#         ("CUDA", CUDA_FLAVOR),
#         ("NON_CUDA", NON_CUDA_FLAVOR),
#     ],
# )
# def test_existing_flavor(
#     populated_secrets: Secrets,
#     session_name: str,
#     expected_flavor: str,
# ):
#     slc_session = SlcSession(session_name)
#     testee = ScriptLanguageContainer(populated_secrets, slc_session=slc_session)
#     expected = FLAVORS_PATH_IN_SLC_REPO / expected_flavor
#     assert testee.flavor_path == str(expected)


def test_create(secrets):
    my_flavor = "Vanilla"
    my_language = "Spanish"
    my_dir = Path("xtest")
    testee = ScriptLanguageContainer.create(
        secrets,
        name="CUDA",
        flavor=my_flavor,
        language_alias=my_language,
    )
    assert secrets.SLC_FLAVOR_CUDA == my_flavor
    assert secrets.SLC_LANGUAGE_ALIAS_CUDA == my_language
    assert Path(secrets.SLC_DIR_CUDA).parts[-2:] == (".slc_checkout", "CUDA")
    assert testee.flavor_path.endswith(my_flavor)


@pytest.mark.parametrize ("key_prefix, description", SESSION_ATTS.items())
def test_missing_property(key_prefix, description):
    """
    Secrets does not contain the specified property for the current SLC
    session.  The test expects ScriptLanguageContainer to raise an
    SlcSessionError.
    """
    session = "CUDA"
    secrets = secrets_without(f"{key_prefix}_{session}")
    with pytest.raises(
        SlcSessionError, match=f"does not contain an {description}"
    ):
        ScriptLanguageContainer(secrets, session)


@pytest.mark.parametrize("name", ["", None])
def test_empty_session_name(name):
    """
    Verify empty string or None are not accepted as name of a
    ScriptLanguageContainer.
    """
    secrets = Mock()
    with pytest.raises(SlcSessionError):
        ScriptLanguageContainer(secrets, name=name)
