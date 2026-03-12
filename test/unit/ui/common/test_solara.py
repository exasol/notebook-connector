"""
Working examples for solara kernel tests
"""

import importlib.resources
from contextlib import contextmanager

import ipywidgets
import solara
from solara.server import reload
from solara.server.app import AppScript

APP_SRC = importlib.resources.files("test.unit.ui.common") / "app.py"
reload.reloader.start()


@contextmanager
def app_box_and_rc(app_name, kernel_context):  # pylint: disable=unused-argument
    """
    Runs and renders a Solara app, yielding `box` (rendered widget tree)
    and `rc` (render context) within a kernel context.
    Ensures app resources are properly closed after execution.
    """

    app = AppScript(str(app_name))
    app.init()
    try:
        with kernel_context:
            # get root widget
            el = app.run()
            root = solara.RoutingProvider(
                children=[el], routes=app.routes, pathname="/"
            )
            # rc = render context
            box, rc = solara.render(root, handle_error=False)
            yield box, rc
    finally:
        app.close()


def test_notebook_widget(
    kernel_context, no_kernel_context
):  # pylint: disable=unused-argument
    """
    The fixture no_kernel_context is not used directly in this test but is required,
    though, to make the test pass.
    """
    with app_box_and_rc(APP_SRC, kernel_context) as (box, rc):
        button = rc.find(ipywidgets.Button).widget
        text = rc.find(ipywidgets.Text).widget
        assert isinstance(button, ipywidgets.Button)
        assert isinstance(text, ipywidgets.Text)
        assert text.value == "init"
        button.click()
        assert text.value == "click"


def test_ipywidgets_update_state():
    """
    Test that clicking an ipywidgets.Button correctly updates a state dictionary
    with the current value of an ipywidgets.Text widget.

    This test simulates user input by setting the value of the Text widget,
    confirms that the state does not update before the button is clicked,
    and then checks that clicking the button updates the state as expected.
    """
    state = {"username": ""}
    textbox = ipywidgets.Text()
    button = ipywidgets.Button(description="Submit")

    def on_click(_):
        state["username"] = textbox.value

    button.on_click(on_click)
    textbox.value = "alice"  # Simulate user input
    assert state["username"] == ""  # asserting state is unchanged
    button.click()  # Simulate button click
    assert state["username"] == "alice"
