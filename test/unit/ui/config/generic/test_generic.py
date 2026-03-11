from unittest.mock import MagicMock

import ipywidgets as widgets
import pytest

from exasol.nb_connector.ui.config import generic


class DummyConfigKey:
    pass


@pytest.fixture
def ui_styles():
    """Provide mock UI styles for widget building."""
    styles = MagicMock()
    styles.button_style = {}
    styles.button_layout = {}
    styles.input_style = {}
    styles.input_layout = {}
    styles.label_style = {}
    styles.label_layout = {}
    styles.row_layout = {}
    styles.header_style = {}
    styles.header_layout = {}
    styles.group_layout = {}
    styles.outer_layout = {}
    return styles


@pytest.fixture
def secrets_store():
    """Provide a mock secrets store."""
    return MagicMock()


@pytest.fixture
def input_definitions():
    """Provide sample widget definitions for two groups."""
    w1 = widgets.Text(value="value1")
    w2 = widgets.Text(value="value2")
    return [[("Label1", w1, DummyConfigKey())], [("Label2", w2, DummyConfigKey())]]


@pytest.fixture
def group_labels():
    """Provide two group labels for the UI."""
    return ["Group1", "Group2"]


def test_generic_configuration_builds_ui(
    monkeypatch, ui_styles, secrets_store, input_definitions, group_labels
):
    """Check that the UI is built with groups and a save button."""
    monkeypatch.setattr(generic, "config_styles", lambda: ui_styles)
    ui = generic.generic_configuration(secrets_store, input_definitions, group_labels)
    assert isinstance(ui, widgets.Box)
    # Should have one save button at the end
    assert isinstance(ui.children[-1], widgets.Button)
    # Should have as many groups as group_names
    assert len(ui.children) == len(group_labels) + 1


def test_save_button_saves_values(
    monkeypatch, ui_styles, secrets_store, input_definitions, group_labels
):
    """Check that clicking save stores all input values."""
    monkeypatch.setattr(generic, "config_styles", lambda: ui_styles)
    ui = generic.generic_configuration(secrets_store, input_definitions, group_labels)
    save_btn = ui.children[-1]
    # Simulate button click
    save_btn.click()
    # Should call save for each input
    assert secrets_store.save.call_count == sum(len(g) for g in input_definitions)
    for group in input_definitions:
        for _, widget, key in group:
            secrets_store.save.assert_any_call(key, str(widget.value))


def test_on_value_change_sets_icon(
    monkeypatch, ui_styles, secrets_store, input_definitions, group_labels
):
    """Check that changing a value sets the pencil icon."""
    monkeypatch.setattr(generic, "config_styles", lambda: ui_styles)
    ui = generic.generic_configuration(secrets_store, input_definitions, group_labels)
    save_btn = ui.children[-1]
    # Simulate value change
    for group in input_definitions:
        for _, widget, _ in group:
            widget.value = widget.value + "x"
    # After value change, icon should be set to "pencil"
    assert save_btn.icon == "pencil"