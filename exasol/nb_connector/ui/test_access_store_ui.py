from exasol.nb_connector.ui.access_store_ui import get_access_store_ui
from IPython.display import display


def test_access_store_ui_screenshot(solara_test, page_session):
    display(get_access_store_ui())
    box_element = page_session.locator(":text('Configuration Store')").locator('..').locator('..')
    box_element.wait_for()
    screenshot = box_element.screenshot()
    with open("./configuration_store_box.png", "wb") as f:
        f.write(screenshot)

