from pathlib import Path

from IPython.display import display

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.main_config_ui import get_db_config_ui, get_db_selection_ui
from test.integration.ui.ui_utils import assert_ui_screenshot

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey, StorageBackend


def create_conf(tmp_path):
    """
    Create a Secret configuration store using a temporary SQLite file.
    """
    scs_file = str(tmp_path / "sample_scs_file.sqlite")
    return Secrets(db_file=Path(scs_file), master_password="password")


def render_main_config_ui(page_session, conf):
    """
    Render the main config UI
    """
    ui = get_db_config_ui(conf=conf)
    display(ui)
    page_session.wait_for_timeout(1000)
    return ui

def render_db_selection_ui(page_session, conf):
    ui = get_db_selection_ui(conf=conf)
    display(ui)
    page_session.wait_for_timeout(1000)
    return ui


def assert_config_ui_screenshot(assert_solara_snapshot, page_session):
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector="button:text('Save')",
        parent_levels=1,
    )
def assert_selection_ui_screenshot(assert_solara_snapshot, page_session):
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector="button:text('Select')",
        parent_levels=1,
    )


def test_default_main_config_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    render_main_config_ui(page_session, conf)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)

def test_onprem_main_config_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    conf.save(CKey.storage_backend, StorageBackend.onprem.name)
    render_main_config_ui(page_session, conf)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)

def test_saas_main_config_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    conf.save(CKey.storage_backend, StorageBackend.saas.name)
    render_main_config_ui(page_session, conf)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)

def test_itde_main_config_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    conf.save(CKey.use_itde, "True")
    render_main_config_ui(page_session, conf)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)

def test_default_db_selection_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    render_db_selection_ui(page_session, conf)
    assert_selection_ui_screenshot(assert_solara_snapshot, page_session)
