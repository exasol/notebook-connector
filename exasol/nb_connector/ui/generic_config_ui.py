from itertools import chain

import ipywidgets as widgets

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.ui_styles import get_config_styles


def get_generic_config_ui(
    secrets: Secrets,
    inputs: list[list[tuple[str, widgets.Widget, CKey]]],
    group_names: list[str],
) -> widgets.Widget:
    """
    The function creates a generic configuration editor UI.
    The UI consists of one or more blocks of configuration data aligned vertically.
    Each block has a header and one or more rows with input fields. Each row has a
    label on the left and one input widget on the right. The form ends with a "Save"
    button, clicking on which results in saving the data in the configuration store.

    Parameters
        conf:        Configuration store
        inputs:      List of the input blocks. Each block is a list of input rows.
                     Each row consists of the label text, input widget, and the key
                     of the corresponding configuration element in the store.
        group_names: Header names for the blocks. The length of this list should
                     match the length of the inputs.
    """

    ui_look = get_config_styles()
    save_btn = widgets.Button(
        description="Save", style=ui_look.button_style, layout=ui_look.button_layout
    )

    def save_configuration(btn):
        for row in chain(*inputs):
            _, widget, key = row
            print("before saving----------------------------------------------------")
            secrets.save(key, str(widget.value))

            print("after saving----------------------------------------------------")
        btn.icon = "check"
        btn.text = "Saved"

    def on_value_change(change):
        save_btn.icon = "pen"
        save_btn.text = "Please Save"

    save_btn.on_click(save_configuration)

    # Apply the styles and layouts to the input fields
    for row in chain(*inputs):
        widget = row[1]
        widget.style = ui_look.input_style
        widget.layout = ui_look.input_layout
        widget.observe(on_value_change, names=["value"])
    # Create a list of lists with input rows
    item_groups = [
        [
            widgets.Box(
                [
                    widgets.Label(
                        value=input_title,
                        style=ui_look.label_style,
                        layout=ui_look.label_layout,
                    ),
                    input_widget,
                ],
                layout=ui_look.row_layout,
            )
            for input_title, input_widget, _ in input_group
        ]
        for input_group in inputs
    ]
    # Create a list of blocks
    items = [
        widgets.Box(
            [
                widgets.Label(
                    value=group_name,
                    style=ui_look.header_style,
                    layout=ui_look.header_layout,
                )
            ]
            + item_group,
            layout=ui_look.group_layout,
        )
        for item_group, group_name in zip(item_groups, group_names)
    ]
    # Add the save button and put everything in an outer Box.
    items.append(save_btn)
    ui = widgets.Box(items, layout=ui_look.outer_layout)
    return ui
