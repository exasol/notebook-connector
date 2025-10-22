import logging
import sys
from pathlib import Path

import ipyvuetify as v
import ipywidgets
import reacton.core

# import pytest
import solara

# import solara.server.app
from solara.server import reload
from solara.server.app import AppScript

logger = logging.getLogger("solara.server.app_test")

HERE = Path(__file__).parent
reload.reloader.start()


def app_box_and_rc(app_name, kernel_context):
    app = AppScript(app_name)
    app.init()
    try:
        with kernel_context:
            el = app.run()
            root = solara.RoutingProvider(
                children=[el], routes=app.routes, pathname="/"
            )
            box, rc = solara.render(root, handle_error=False)
            yield box, rc
    finally:
        app.close()


def test_notebook_widget(kernel_context, no_kernel_context):
    name = str(HERE / "app.py")
    for box, rc in app_box_and_rc(name, kernel_context):
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
    # Simulate user input
    textbox.value = "alice"
    assert global_state["username"] == ""
    # Simulate button click by calling event handler
    button.click()
    # Alternatively, you can call the handler directly if you saved it
    # Assert
    assert global_state["username"] == "alice"
