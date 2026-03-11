from IPython.display import display

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.ui.config.db_selection import select_db_backend
from exasol.nb_connector.ui.config.main import (
    configure_db,
)


def render_main_config_ui(page_session, conf):
    """
    Render the main config UI
    """
    ui = configure_db(conf=conf)
    display(ui)
    page_session.wait_for_timeout(1000)
    return ui


def render_db_selection_ui(page_session, conf):
    ui = select_db_backend(conf=conf)
    display(ui)
    page_session.wait_for_timeout(1000)
    return ui


def render_onprem_non_itde_ui(page_session, secrets):
    secrets.save(CKey.use_itde, "False")
    render_main_config_ui(page_session, secrets)


def render_saas_ui(page_session, secrets):
    secrets.save(CKey.storage_backend, StorageBackend.saas.name)
    render_main_config_ui(page_session, secrets)
