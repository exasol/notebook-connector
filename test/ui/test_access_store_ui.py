from exasol.nb_connector.ui.access_store_ui import get_access_store_ui
from IPython.display import display

def test_access_store_ui_screenshot(solara_test, page_session, assert_solara_snapshot,playwright):
    display(get_access_store_ui())
    box_element = page_session.locator(":text('Configuration Store')").locator('..').locator('..')
    box_element.wait_for()
    assert_solara_snapshot(box_element.screenshot())

def test_enter_password_and_click_open(solara_test, page_session,assert_solara_snapshot):
    display(get_access_store_ui())
    password_input = page_session.locator("input[type='password']")
    password_input.wait_for()
    password_input.fill("dummy123")

    open_button = page_session.locator("button:text('Open')")
    open_button.wait_for()
    open_button.click()

    page_session.wait_for_timeout(1000)

    box_element = page_session.locator(":text('Configuration Store')").locator('..').locator('..')
    box_element.wait_for()
    assert_solara_snapshot(box_element.screenshot())