from unittest.mock import MagicMock

import ipywidgets as widgets
import pytest

from exasol.nb_connector.ui.config import db_selection


@pytest.fixture
def config_store():
    """Create a mock config store with default settings."""
    conf = MagicMock()
    conf.get.side_effect = lambda key, default=None: {"use_itde": "True"}.get(
        key, default
    )
    return conf


@pytest.fixture
def ui_styles():
    """Provide default UI styles for tests."""

    class UILook:
        input_layout = widgets.Layout()
        input_style = {}
        button_style = widgets.ButtonStyle()
        button_layout = widgets.Layout()
        header_style = {}
        header_layout = widgets.Layout()
        row_layout = widgets.Layout()
        group_layout = widgets.Layout()
        outer_layout = widgets.Layout()

    return UILook()


def _assert_layout_has_controls(ui):
    """Check the UI has a button and a container box."""
    assert isinstance(ui, widgets.Box)
    assert any(isinstance(child, widgets.Button) for child in ui.children)
    assert any(isinstance(child, widgets.Box) for child in ui.children)


def test_select_db_backend_docker_db(monkeypatch, config_store, ui_styles):
    """Select Docker DB when on-prem backend and use_itde is True."""
    monkeypatch.setattr(
        db_selection, "get_backend", lambda _: db_selection.StorageBackend.onprem
    )
    monkeypatch.setattr(db_selection, "config_styles", lambda: ui_styles)

    # use_itde True, should select Docker-DB
    ui = db_selection.select_db_backend(config_store)
    _assert_layout_has_controls(ui)


def test_select_db_backend_onprem(monkeypatch, config_store, ui_styles):
    """Select on-prem DB when on-prem backend and use_itde is False."""
    monkeypatch.setattr(
        db_selection, "get_backend", lambda _: db_selection.StorageBackend.onprem
    )
    monkeypatch.setattr(db_selection, "config_styles", lambda: ui_styles)
    config_store.get.side_effect = lambda key, default=None: {"use_itde": "False"}.get(
        key, default
    )

    # use_itde False, should select On-Prem
    ui = db_selection.select_db_backend(config_store)
    _assert_layout_has_controls(ui)


def test_select_db_backend_saas(monkeypatch, config_store, ui_styles):
    """Select SaaS DB when backend is SaaS."""
    monkeypatch.setattr(
        db_selection, "get_backend", lambda _: db_selection.StorageBackend.saas
    )
    monkeypatch.setattr(db_selection, "config_styles", lambda: ui_styles)

    # Should select SaaS
    ui = db_selection.select_db_backend(config_store)
    _assert_layout_has_controls(ui)


def test_select_database_button_click(monkeypatch, config_store, ui_styles):
    """Clicking the button should set the check icon."""
    monkeypatch.setattr(
        db_selection, "get_backend", lambda _: db_selection.StorageBackend.saas
    )
    monkeypatch.setattr(db_selection, "config_styles", lambda: ui_styles)

    ui = db_selection.select_db_backend(config_store)
    # Find the button and simulate click
    button = [c for c in ui.children if isinstance(c, widgets.Button)][0]
    # Icon should be empty before click
    assert button.icon == ""
    button.click()  # Use the public click method to trigger the event
    # Icon should be "check" after click
    assert button.icon == "check"


def test_radio_value_change_sets_icon(monkeypatch, config_store, ui_styles):
    """Changing the radio value should set the pencil icon."""
    monkeypatch.setattr(
        db_selection, "get_backend", lambda _: db_selection.StorageBackend.saas
    )
    monkeypatch.setattr(db_selection, "config_styles", lambda: ui_styles)

    ui = db_selection.select_db_backend(config_store)
    button = [c for c in ui.children if isinstance(c, widgets.Button)][0]
    group_box = [c for c in ui.children if isinstance(c, widgets.Box)][0]
    # The group_box contains [Label, Box([RadioButtons])]
    radio_box = [w for w in group_box.children if isinstance(w, widgets.Box)]
    assert radio_box, "RadioButtons container Box not found"
    radio = [w for w in radio_box[0].children if isinstance(w, widgets.RadioButtons)][0]
    # Icon should be empty before change
    assert button.icon == ""
    # Simulate value change
    radio.value = radio.options[1]
    # Should set button.icon to "pencil" via observer
    assert button.icon == "pencil"
