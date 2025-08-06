from pathlib import Path
from test.unit.slc.util import (
    SESSION_ATTS,
    secrets_without,
)

import pytest

from exasol.nb_connector.slc import constants
from exasol.nb_connector.slc.slc_session import (
    SlcSession,
    SlcSessionError,
)


@pytest.mark.parametrize("prefix, description", SESSION_ATTS.items())
def test_missing_properties(sample_session, prefix, description):
    secrets = secrets_without(sample_session, prefix)
    testee = SlcSession(secrets=secrets, name=sample_session)
    with pytest.raises(
        SlcSessionError,
        match=f"does not contain an {description}",
    ):
        testee.verify()


def test_properties(secrets):
    session = SlcSession(secrets=secrets, name="my_session")
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
    expected_flavor_path = constants.FLAVORS_PATH_IN_SLC_REPO / my_flavor
    assert session.flavor_path_in_slc_repo == expected_flavor_path
    expected_flavor_dir = my_dir / expected_flavor_path
    assert session.flavor_dir == expected_flavor_dir
    assert session.custom_pip_file == (
        expected_flavor_dir
        / "flavor_customization"
        / "packages"
        / "python3_pip_packages"
    )
