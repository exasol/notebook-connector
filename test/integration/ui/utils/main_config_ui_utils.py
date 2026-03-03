from test.integration.ui.utils.ui_utils import assert_ui_screenshot

from IPython.display import display

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.ui.main_config_ui import (
    get_db_config_ui,
    get_db_selection_ui,
)


def assert_main_config_ui_screenshot(assert_solara_snapshot, page_session):
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


def render_onprem_non_itde_ui(page_session, secrets):
    secrets.save(CKey.use_itde, "False")
    render_main_config_ui(page_session, secrets)


def render_saas_ui(page_session, secrets):
    secrets.save(CKey.storage_backend, StorageBackend.saas.name)
    render_main_config_ui(page_session, secrets)
