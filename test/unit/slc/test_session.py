from pathlib import Path
import pytest

from exasol.nb_connector.slc import constants
from exasol.nb_connector.slc.slc_session import SlcSession


def test_properties(secrets):
    my_slc_name = "MY_SLC"
    session = SlcSession(secrets=secrets, name=my_slc_name)
    my_flavor = "Vanilla"
    my_dir = Path("xtest")
    session.save(
        flavor=my_flavor,
        checkout_dir=my_dir,
    )
    assert session.flavor == my_flavor
    assert session.language_alias == my_slc_name
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
