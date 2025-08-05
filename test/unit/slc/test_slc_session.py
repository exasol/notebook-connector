from pathlib import Path

from exasol.nb_connector.slc.constants import FLAVORS_PATH_IN_SLC_REPO
from exasol.nb_connector.slc.slc_session import SlcSession


def test_properties(secrets):
    session = SlcSession(secrets=secrets, name="my_session")
    my_flavor = "Vanilla"
    my_alias = "longus"
    my_dir = Path("xtest")
    session.save(
        flavor_name=my_flavor,
        language_alias=my_alias,
        checkout_dir=my_dir,
    )
    assert session.flavor_name == my_flavor
    assert session.language_alias == my_alias
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
