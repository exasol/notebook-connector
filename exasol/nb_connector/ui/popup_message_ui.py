import ipywidgets as widgets
from IPython.display import (
    Javascript,
    clear_output,
    display,
)

# Prepare to display a popup message
notify_output = widgets.Output()
display(notify_output)


@notify_output.capture()
def popup_message(message):
    clear_output()
    message = message.replace("'", '"')
    display(Javascript(f"alert('{message}')"))
