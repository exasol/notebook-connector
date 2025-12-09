"""
Utility for rendering Solara apps for testing purposes.
"""

from contextlib import contextmanager

import solara
from solara.server.app import AppScript


@contextmanager
def app_box_and_rc(app_name, kernel_context):
    """
    Context manager to initialize and render a Solara app for testing.

    Args:
        app_name (str): Name or path of the Solara app script.
        kernel_context: The kernel context to run the app in.

    Yields:
        box: The Solara root box widget.
        rc: The rendered components (rc) for widget queries.
    """
    app = AppScript(str(app_name))
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
