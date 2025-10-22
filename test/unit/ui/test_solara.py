import logging
from pathlib import Path

import ipywidgets
import solara
from solara.server import reload
from solara.server.app import AppScript
import importlib.resources
from contextlib import contextmanager

logger = logging.getLogger("solara.server.app_test")

APP_SRC = importlib.resources.files("test.unit.ui") / "app.py"
reload.reloader.start()

@contextmanager
def app_box_and_rc(app_name, kernel_context):
    app = AppScript(app_name)
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


def test_notebook_widget(kernel_context, no_kernel_context):
    """
    The fixture no_kernel_context is not used directly in this test but is required, though, to
    make the test pass.
    """
    print("JS23",APP_SRC)
    with app_box_and_rc(APP_SRC, kernel_context) as (box, rc):
        button = rc.find(ipywidgets.Button).widget
        text = rc.find(ipywidgets.Text).widget
        assert isinstance(button, ipywidgets.Button)
        assert isinstance(text, ipywidgets.Text)
        assert text.value == "init"
        button.click()
        assert text.value == "click"


def test_ipywidgets_update_global_state():
    import ipywidgets as widgets

    global_state = {"username": ""}
    textbox = widgets.Text()
    button = widgets.Button(description="Submit")

    def on_click(b):
        global_state["username"] = textbox.value

    button.on_click(on_click)
    textbox.value = "alice" # Simulate user input
    assert global_state["username"] == "" # assert global state is unchanged
    button.click() # Simulate button click
    assert global_state["username"] == "alice" 
