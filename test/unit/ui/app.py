"""
TODO: docstring
"""
import ipywidgets

text = ipywidgets.Text(value="init")
button = ipywidgets.Button(description="Click me")


def on_button_clicked(b):
    text.value = "click"


button.on_click(on_button_clicked)
app = ipywidgets.VBox([text, button])
