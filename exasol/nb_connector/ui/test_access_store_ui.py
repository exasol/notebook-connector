from exasol.nb_connector.ui.access_store_ui import get_access_store_ui
from IPython.display import display
import solara
from IPython import get_ipython

def test_access_store_ui_screenshot(solara_test, page_session, assert_solara_snapshot):
    # get_ipython().run_line_magic('store', '-r')
    display(get_access_store_ui())
    box_element = page_session.locator(":text('Configuration Store')").locator('..').locator('..')
    box_element.wait_for()
    screenshot = box_element.screenshot()
    with open("./configuration_store_box.png", "wb") as f:
        f.write(screenshot)

    # postfix = "-ipyvuetify3" if getattr(solara.util, "ipyvuetify_major_version", 0) == 3 else ""
    # assert_solara_snapshot(screenshot, postfix=postfix)
