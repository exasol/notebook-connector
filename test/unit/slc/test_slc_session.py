from pathlib import Path
from test.unit.slc.util import secrets_without
from unittest.mock import (
    Mock,
    create_autospec,
)

import pytest

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.constants import FLAVORS_PATH_IN_SLC_REPO
from exasol.nb_connector.slc.slc_session import (
    SlcSession,
    SlcSessionError,
)

SESSION_ATTS = {
    "SLC_FLAVOR": "SLC flavor",
    "SLC_LANGUAGE_ALIAS": "SLC language alias",
    "SLC_DIR": "SLC working directory",
}

@pytest.mark.parametrize(
    "prefix, description", SESSION_ATTS.items()
)
def test_missing_properties(prefix, description):
    session = "my_session"
    secrets = secrets_without(f"{prefix}_{session}")
    with pytest.raises(
        SlcSessionError, match=f"does not contain an {description}",
    ):
        SlcSession(secrets=secrets, name=session)


def test_properties(secrets):
    session = SlcSession(secrets=secrets, name="my_session", verify=False)
    my_flavor = "Vanilla"
    my_language = "Spanish"
    my_dir = Path("xtest")
    session.save(
        flavor=my_flavor,
        language_alias=my_language,
        checkout_dir=my_dir,
    )
    assert session.flavor == my_flavor
    assert session.language_alias == my_language
    assert session.checkout_dir == my_dir
    my_path = FLAVORS_PATH_IN_SLC_REPO / my_flavor
    assert session.flavor_path_in_slc_repo == my_path
    my_dir = my_dir / my_path
    assert session.flavor_dir == my_dir
    assert session.custom_pip_file == (
        my_dir
        / "flavor_customization"
        / "packages"
        / "python3_pip_packages"
    )
