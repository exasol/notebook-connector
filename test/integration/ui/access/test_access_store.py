from pathlib import Path
from test.integration.ui.common.utils.ui_utils import CONF_STORE

import nbformat
from IPython.display import display
from nbclient import NotebookClient

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.access.access_store import (
    DEFAULT_FILE_NAME,
    get_access_store,
)


def fill_scs_password(password: str, page_session):
    password_field = page_session.locator("input[type='password']")
    password_field.fill(password)


def fill_scs_file_name(scs_file: str, page_session):
    scs_file_textfield = page_session.locator("input[type='text']")
    scs_file_textfield.fill(scs_file)


def click_open_db(page_session):
    open_button = page_session.locator("button:text('Open')")
    open_button.click()


def verify_content(password: str, scs_file: Path):
    """checking if the file has the correct content"""
    secrets = Secrets(db_file=scs_file, master_password=password)
    assert not list(secrets.keys())


def test_access_store_ui_screenshot(solara_test, page_session, ui_screenshot, tmp_path):
    """Check that get_access_store_ui displays the access store UI elements."""
    display(get_access_store(str(tmp_path)))
    ui_screenshot(anchor_selector=CONF_STORE, parent_levels=2)


def test_enter_password_and_click_open(
    solara_test, page_session, ui_screenshot, tmp_path
):
    """Validate that clicking Open with a password creates the default secure store file."""
    code_word = "dummy123"
    display(get_access_store(str(tmp_path)))
    fill_scs_password(code_word, page_session)
    click_open_db(page_session)
    ui_screenshot(anchor_selector=CONF_STORE, parent_levels=2)
    generated_scs_file = tmp_path / DEFAULT_FILE_NAME
    assert generated_scs_file.exists()
    assert not list(Secrets(generated_scs_file, code_word).keys())


def test_non_default_store_file(solara_test, page_session, ui_screenshot, tmp_path):
    """Validate that a non-default secure store file can be created and opened with the correct password."""
    code_word = "dummy123"
    scs_file = "ai_lab_secure_dummy.sqlite"
    display(get_access_store(str(tmp_path)))
    fill_scs_file_name(scs_file, page_session)
    fill_scs_password(code_word, page_session)
    click_open_db(page_session)
    ui_screenshot(anchor_selector=CONF_STORE, parent_levels=2)
    generated_scs_file = tmp_path / scs_file
    assert generated_scs_file.exists()
    assert not list(Secrets(generated_scs_file, code_word).keys())


def test_invalid_password(solara_test, page_session, ui_screenshot, tmp_path):
    """Validate that opening an existing secure store with a wrong password shows an error state in the UI."""
    scs_file = "sample.scs_file"
    secrets = Secrets(db_file=tmp_path / scs_file, master_password="abc")
    secrets.save("abc_key", "abc_value")
    display(get_access_store(str(tmp_path)))
    fill_scs_file_name(scs_file, page_session)
    fill_scs_password("wrong_password", page_session)
    click_open_db(page_session)
    ui_screenshot(anchor_selector=CONF_STORE, parent_levels=2)


def test_access_store_sets_ai_lab_config_in_ipython(tmp_path):
    code_word = "dummy123"
    store_dir = str(tmp_path)

    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_code_cell(
            f"""
            from exasol.nb_connector.ui.access.access_store import get_access_store
            
            ui = get_access_store("{store_dir}")
            display(ui)
            
            password_field = ui.children[0].children[2].children[1]
            password_field.value = "{code_word}"
            open_button = ui.children[1]
            open_button.click()
            
            """
        ),
        nbformat.v4.new_code_cell(
            """
                ai_lab_config
            """
        ),
    ]

    NotebookClient(nb, timeout=60, kernel_name="python3").execute()
