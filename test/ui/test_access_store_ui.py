import pytest

from exasol.nb_connector.ui.access_store_ui import get_access_store_ui
from IPython.display import display



def test_access_store_ui_screenshot(solara_test, page_session):
    display(get_access_store_ui())
    box_element = page_session.locator(":text('Configuration Store')").locator('..').locator('..')
    box_element.wait_for()
    screenshot = box_element.screenshot()
    with open("./configuration_store_box.png", "wb") as f:
        f.write(screenshot)

    with open("./configuration_store_box.png", "rb") as f:
        image_data = f.read()
    assert image_data == screenshot

def test_enter_password_and_click_open(solara_test, page_session):
    display(get_access_store_ui())
    password_input = page_session.locator("input[type='password']")
    password_input.wait_for()
    password_input.fill("dummy123")

    open_button = page_session.locator("button:text('Open')")
    open_button.wait_for()
    open_button.click()

    with open("./ai_lab_secure_configuration_storage.sqlite", "rb") as f:
        data = f.read()
    assert data
