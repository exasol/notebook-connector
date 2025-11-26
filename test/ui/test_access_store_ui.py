import pytest

from exasol.nb_connector.secret_store import Secrets, InvalidPassword
from exasol.nb_connector.ui.access_store_ui import get_access_store_ui
from IPython.display import display
from pathlib import Path

def assert_screenshot(assert_solara_snapshot, page_session):
    page_session.wait_for_timeout(1000)
    box_element = page_session.locator(":text('Configuration Store')").locator('..').locator('..')
    box_element.wait_for()
    assert_solara_snapshot(box_element.screenshot())


def fill_store_password(dummy_password: str, page_session):
    password_input = page_session.locator("input[type='password']")
    password_input.wait_for()
    password_input.fill(dummy_password)


def fill_store_file_name(dummy_sb_store_file: str, page_session):
    sb_store_file_input = page_session.locator("input[type='text']")
    sb_store_file_input.fill(dummy_sb_store_file)


def open_db(page_session):
    open_button = page_session.locator("button:text('Open')")
    open_button.wait_for()
    open_button.click()


def verify_content(dummy_password: str, generated_db_file: Path):
    # checking if the file has the correct content
    secrets = Secrets(db_file=generated_db_file, master_password=dummy_password)
    assert list(secrets.keys()) == []


def is_sb_file_exists(generated_db_file_path : str) -> Path:
    # checking if the file is created
    generated_db_file = Path(generated_db_file_path)
    generated_db_file_exists = generated_db_file.exists()
    assert generated_db_file_exists
    return generated_db_file

def test_access_store_ui_screenshot(solara_test, page_session, assert_solara_snapshot,playwright,tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    display(get_access_store_ui())
    box_element = page_session.locator(":text('Configuration Store')").locator('..').locator('..')
    box_element.wait_for()
    assert_solara_snapshot(box_element.screenshot())

def test_enter_password_and_click_open(solara_test, page_session,assert_solara_snapshot,tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    dummy_password = "dummy123"
    display(get_access_store_ui())
    password_input = page_session.locator("input[type='password']")
    password_input.wait_for()
    password_input.fill(dummy_password)
    open_db(page_session)
    assert_screenshot(assert_solara_snapshot, page_session)
    generated_db_file = is_sb_file_exists("ai_lab_secure_configuration_storage.sqlite")
    verify_content(dummy_password, generated_db_file)

def test_non_default_store_file(solara_test, page_session,assert_solara_snapshot,tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    dummy_password = "dummy123"
    dummy_sb_store_file = "ai_lab_secure_dummy.sqlite"
    display(get_access_store_ui())
    fill_store_file_name(dummy_sb_store_file, page_session)
    fill_store_password(dummy_password, page_session)
    open_db(page_session)
    assert_screenshot(assert_solara_snapshot, page_session)
    generated_db_file = is_sb_file_exists(dummy_sb_store_file)
    verify_content(dummy_password, generated_db_file)

def test_invalid_store_password(solara_test, page_session,assert_solara_snapshot,tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(InvalidPassword) as exception:
        dummy_password = "dummy123"
        dummy_sb_store_file = "ai_lab_invalid_dummy.sqlite"
        display(get_access_store_ui())
        fill_store_file_name(dummy_sb_store_file, page_session)
        fill_store_password(dummy_password, page_session)
        open_db(page_session)
        assert_screenshot(assert_solara_snapshot, page_session)
        generated_db_file = is_sb_file_exists(dummy_sb_store_file)
        verify_content(dummy_password+'4', generated_db_file)
    assert "master password is incorrect" in str(exception.value)