from IPython.display import display

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.generic_config_ui import get_generic_config_ui


def test_generic_config_ui_load(
    solara_test, page_session, assert_solara_snapshot, tmp_path
):
    scs_file = str(tmp_path / "sample_scs_file.sqlite")
    conf = Secrets(db_file=scs_file, master_password="password")
    inputs = []
    group_names = []
    ui = get_generic_config_ui(conf=conf, inputs=inputs, group_names=group_names)
    display(ui)
    page_session.wait_for_timeout(1000)
    screenshot = page_session.screenshot()
    assert_solara_snapshot(screenshot)
