"""
A simple ipywidgets application demonstrating interactive widget behavior.
This file is being called from test_solara.py

This module defines a basic user interface with a text box and a button using ipywidgets.
The text box is initially set to "init". When the button is clicked, the text box's value
is updated to "click" via an event handler. The widgets are combined in a vertical box (VBox)
layout and exposed as the variable `app` for integration with other systems or testing.

Widgets:
- Text: Displays a string, initially "init".
- Button: When clicked, sets the text widget's value to "click".
"""

import ipywidgets

text = ipywidgets.Text(value="init")
button = ipywidgets.Button(description="Click me")


def on_button_clicked(b):
    text.value = "click"


button.on_click(on_button_clicked)
app = ipywidgets.VBox([text, button])
