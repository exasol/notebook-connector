from pathlib import Path

from IPython.display import display

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.access_store_ui import (
    DEFAULT_FILE_NAME,
    get_access_store_ui,
)


def assert_screenshot(assert_solara_snapshot, page_session):
    """
    Creates an actual screenshot and asserts if the screenshot is identical to the
    expectation. The expected screenshots are located in folder ui_screenshots.
    If the actual screenshot differs from the expected, then solara save the
    actual to folder test-results for comparison. You can also decide to copy
    the actual as expected to make the test succeed next time,
    see the developer guide for details.
    """
    # wait for the page to load before finding the element in UI followed
    # by screenshot assertion.
    # As of now, we didn't find another way to wait for the action.
    page_session.wait_for_timeout(1000)
    box_element = (
        page_session.locator(":text('Configuration Store')").locator("..").locator("..")
    )
    box_element.wait_for()
    assert_solara_snapshot(box_element.screenshot())


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


def test_access_store_ui_screenshot(
    solara_test, page_session, assert_solara_snapshot, tmp_path
):
    """
    test to check if the get_access_store_ui function displays the UI elements
    """
    display(get_access_store_ui(str(tmp_path)))
    assert_screenshot(assert_solara_snapshot, page_session)


def test_enter_password_and_click_open(
    solara_test, page_session, assert_solara_snapshot, tmp_path
):
    """
    test to validate if the open button is pressed and file is created
    """
    password = "dummy123"
    display(get_access_store_ui(str(tmp_path)))
    password_field = page_session.locator("input[type='password']")
    password_field.fill(password)
    click_open_db(page_session)
    assert_screenshot(assert_solara_snapshot, page_session)
    generated_scs_file = tmp_path / DEFAULT_FILE_NAME
    assert generated_scs_file.exists()
    assert not list(Secrets(generated_scs_file, password).keys())


def test_non_default_store_file(
    solara_test, page_session, assert_solara_snapshot, tmp_path
):
    """
    test to validate if the file accepts the correct password
    """
    password = "dummy123"
    scs_file = "ai_lab_secure_dummy.sqlite"
    display(get_access_store_ui(str(tmp_path)))
    fill_scs_file_name(scs_file, page_session)
    fill_scs_password(password, page_session)
    click_open_db(page_session)
    assert_screenshot(assert_solara_snapshot, page_session)
    generated_scs_file = tmp_path / scs_file
    assert generated_scs_file.exists()
    assert not list(Secrets(generated_scs_file, password).keys())


def test_invalid_password(solara_test, page_session, assert_solara_snapshot, tmp_path):
    """
    test to validate if the file fails to accept the wrong password
    """
    scs_file = "sample.scs_file"
    secrets = Secrets(db_file=tmp_path / scs_file, master_password="abc")
    secrets.save("abc_key", "abc_value")
    display(get_access_store_ui(str(tmp_path)))
    fill_scs_file_name(scs_file, page_session)
    fill_scs_password("wrong_password", page_session)
    click_open_db(page_session)
    # take screenshot
    assert_screenshot(assert_solara_snapshot, page_session)
