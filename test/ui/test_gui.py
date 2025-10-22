import ipywidgets as widgets
import playwright.sync_api
import solara
from IPython.display import display


def test_widget_button_solara(
    solara_test, page_session: playwright.sync_api.Page, assert_solara_snapshot
):
    # this all runs in process, which only works with solara
    # also, this test is only with pure ipywidgets
    button = widgets.Button(description="Click Me!")

    def change_description(obj):
        button.description = "Tested event"

    button.on_click(change_description)
    display(button)
    button_sel = page_session.locator("text=Click Me!")
    button_sel.wait_for()
    button_sel.click()
    page_session.locator("text=Tested event").wait_for()
    # with ipyvuetify 2 we modified the button font for ipywidgets, that does not happen anymore with ipyvuetify 3
    # therefore we have a different screenshot for ipyvuetify 2 and 3
    assert_solara_snapshot(
        page_session.locator("text=Tested event").screenshot(),
        postfix="-ipyvuetify3" if solara.util.ipyvuetify_major_version == 3 else "",
    )
