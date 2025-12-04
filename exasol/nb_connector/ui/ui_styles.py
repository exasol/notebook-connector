"""
The UI design aims to provide a convenient way of setting up various configuration parameters.
A user form would consist of one or more blocks of data laid out vertically or horizontally. The positioning of these blocks is defined by the `outer_layout` property.
A block includes a collection of UI elements. Each element is represented by a pair of widgets - a Label with the description of an element and the input widget, e.g. a Text. The layout of the elements within the block is defined by the `group_layout` property.
The layout of the description Label and the input widget is defined by the `row_layout` property. As the name suggests, an input and its description are assumed to be placed next to one another in a row, although such design is not strictly required.
A block may include a header Label where one can put the name of the input data group. `header_style` and `header_layout` define respectively the style and the layout of such labels.
Likewise, the Labels of input elements have their style and layout defined by the `label_style` and `label_layout` properties. The input elements themselves have similar properties - `input_style` and `input_layout`.
A user form may include one or more buttons. Their style and layout are defined as `button_style` and `button_layout`.
"""

SOLID_BORDER: str = "solid 1px"


def get_config_styles():

    from dataclasses import (
        dataclass,
        field,
    )

    import ipywidgets as widgets

    @dataclass(frozen=True)
    class UiLook:
        header_style: dict = field(default_factory=dict)
        header_layout: widgets.Layout = field(default_factory=widgets.Layout)
        label_style: dict = field(default_factory=dict)
        label_layout: widgets.Layout = field(default_factory=widgets.Layout)
        input_style: dict = field(default_factory=dict)
        input_layout: widgets.Layout = field(default_factory=widgets.Layout)
        button_style: dict = field(default_factory=dict)
        button_layout: widgets.Layout = field(default_factory=widgets.Layout)
        row_layout: widgets.Layout = field(default_factory=widgets.Layout)
        group_layout: widgets.Layout = field(default_factory=widgets.Layout)
        outer_layout: widgets.Layout = field(default_factory=widgets.Layout)

    return UiLook(
        header_style={"background": "Beige"},
        header_layout=widgets.Layout(
            display="flex", justify_content="center", border=SOLID_BORDER
        ),
        label_layout=widgets.Layout(max_width="130px"),
        input_layout=widgets.Layout(max_width="200px"),
        button_style={"button_color": "LightCyan"},
        button_layout=widgets.Layout(border=SOLID_BORDER, margin="12px 0 0 0"),
        row_layout=widgets.Layout(
            display="flex",
            flex_flow="row",
            max_width="350px",
            justify_content="space-between",
            padding="0 0 0 10px",
        ),
        group_layout=widgets.Layout(
            display="flex",
            flex_flow="column",
            border=SOLID_BORDER,
            max_width="350px",
            margin="12px 0 0 0",
        ),
        outer_layout=widgets.Layout(
            display="flex",
            flex_flow="column",
            align_items="stretch",
            padding="0 0 0 50px",
        ),
    )
