import ipywidgets as widgets
import playwright.sync_api
import solara
from IPython.display import display
import ipyvuetify



def test_widget_button_solara(
    solara_test, page_session: playwright.sync_api.Page, assert_solara_snapshot
):
    """
       Test that clicking an ipywidgets.Button updates its description.

       Simulates a button click in a browser using Playwright, checks that the button text
       changes as expected, and verifies the result with a UI snapshot.
       """
    button = widgets.Button(description="Click Me!")

    def change_description(obj):
        button.description = "Tested event"

    button.on_click(change_description)
    display(button)
    button_sel = page_session.locator("text=Click Me!")
    button_sel.wait_for()
    button_sel.click()
    page_session.locator("text=Tested event").wait_for()
    assert_solara_snapshot(
        page_session.locator("text=Tested event").screenshot(),
        postfix="-ipyvuetify3" if solara.util.ipyvuetify_major_version == 3 else "",
    )
