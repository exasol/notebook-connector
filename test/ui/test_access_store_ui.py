from pathlib import Path
from unittest.mock import (
    MagicMock,
    patch,
)

from IPython.display import display

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.access_store_ui import get_access_store_ui


def assert_screenshot(assert_solara_snapshot, page_session):
    """
    Creates an actual screenshot and asserts if the screenshot is identical to the expectation.
    The expected screenshots are located in folder ui_screenshots.
    If the actual screenshot differs from the expected, then solara save the actual to folder
    test-results for comparison. You can also decide to copy the actual as expected to make
    the test succeed next time, see the developer guide for details.
    """    
    page_session.wait_for_timeout(1000)
    box_element = (
        page_session.locator(":text('Configuration Store')").locator("..").locator("..")
    )
    box_element.wait_for()
    assert_solara_snapshot(box_element.screenshot())


def fill_store_password(password: str, page_session):
    password_input = page_session.locator("input[type='password']")
    password_input.wait_for()
    password_input.fill(dummy_password)


def fill_store_file_name(dummy_db_store_file: str, page_session):
    db_store_file_input = page_session.locator("input[type='text']")
    db_store_file_input.fill(dummy_db_store_file)


def click_open_db(page_session):
    open_button = page_session.locator("button:text('Open')")
    open_button.wait_for()
    open_button.click()


def verify_content(dummy_password: str, generated_db_file: Path):
    """checking if the file has the correct content"""
    secrets = Secrets(db_file=generated_db_file, master_password=dummy_password)
    assert list(secrets.keys()) == []


def is_db_file_exists(generated_db_file_path: str) -> Path:
    """checking if the file is created"""
    generated_db_file = Path(generated_db_file_path)
    generated_db_file_exists = generated_db_file.exists()
    assert generated_db_file_exists
    return generated_db_file


def test_access_store_ui_screenshot(
    solara_test, page_session, assert_solara_snapshot, playwright, tmp_path
):
    """
    test to check if the get_access_store_ui function displays the UI elements
    """
    display(get_access_store_ui(str(tmp_path)))
    box_element = (
        page_session.locator(":text('Configuration Store')").locator("..").locator("..")
    )
    box_element.wait_for()
    assert_solara_snapshot(box_element.screenshot())


def test_enter_password_and_click_open(
    solara_test, page_session, assert_solara_snapshot, tmp_path
):
    """
    test to validate if the open button is pressed and file is created
    """
    dummy_password = "dummy123"
    display(get_access_store_ui(str(tmp_path)))
    password_input = page_session.locator("input[type='password']")
    password_input.wait_for()
    password_input.fill(dummy_password)
    click_open_db(page_session)
    assert_screenshot(assert_solara_snapshot, page_session)
    assert Secrets(dummy_password, generated_db_file).keys() == []


def test_non_default_store_file(
    solara_test, page_session, assert_solara_snapshot, tmp_path
):
    """
    test to validate if the file accepts the correct password
    """
    dummy_password = "dummy123"
    dummy_db_store_file = "ai_lab_secure_dummy.sqlite"
    display(get_access_store_ui(str(tmp_path)))
    fill_store_file_name(dummy_db_store_file, page_session)
    fill_store_password(dummy_password, page_session)
    click_open_db(page_session)
    assert_screenshot(assert_solara_snapshot, page_session)
    generated_db_file = is_db_file_exists(str(tmp_path / dummy_db_store_file))
    verify_content(dummy_password, generated_db_file)


def test_invalid_password(
    solara_test, page_session, assert_solara_snapshot, tmp_path
):
    """
    test to validate if the file fails to accept the wrong password
    """
    sqlite = "sample.sqlite"
    secrets = Secrets(db_file=tmp_path / sqlite, master_password="abc")
    secrets.save("abc_key", "abc_value")
    display(get_access_store_ui(str(tmp_path)))
    fill_store_file_name(sqlite, page_session)
    fill_store_password("wrong_password", page_session)
    click_open_db(page_session)
    # take screenshot
    page_session.wait_for_timeout(1000)
    assert_screenshot(assert_solara_snapshot, page_session)


def test_run_line_magic_store_called():
    """
    test to validate if the run_line_magic function calls store magic
    """
    mock_ipython = MagicMock()
    with patch(
        "exasol.nb_connector.ui.access_store_ui.get_ipython", return_value=mock_ipython
    ):
        get_access_store_ui()
        # assert using assert_called_once_with
        mock_ipython.run_line_magic.assert_called_once_with("store", "-r")
