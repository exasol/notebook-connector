from pathlib import Path
from test.conftest import secrets
from test.integration.ui.utils.ui_utils import (
    SAVE_BUTTON,
    assert_ui_screenshot,
    click_save,
    expect_save_button_to_have_pencil_icon,
    fill_text,
    save_button,
    set_checkbox,
)
from typing import Optional

import ipywidgets as widgets
import pytest
from IPython.display import display

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.generic_config_ui import get_generic_config_ui


@pytest.fixture
def inputs_and_groups():
    """
    input grouped widget definitions and their group names for the generic config UI.
    """
    inputs = [
        [
            ("Host", widgets.Text(value="localhost"), CKey.db_host_name),
            ("Port", widgets.IntText(value=8563), CKey.db_port),
        ],
        [
            ("User", widgets.Text(value="sys"), CKey.db_user),
        ],
        [
            ("Encrypted Comm.", widgets.Checkbox(value=False), CKey.db_encryption),
        ],
    ]
    group_names = ["Connection", "Credentials", "Encryption"]
    return inputs, group_names


def create_conf(tmp_path):
    """
    Create a Secret configuration store using a temporary SQLite file.
    """
    scs_file = str(tmp_path / "sample_scs_file.sqlite")
    return Secrets(db_file=Path(scs_file), master_password="password")


def render_ui(page_session, conf, inputs, group_names):
    """
    Render the generic config UI
    """
    ui = get_generic_config_ui(secrets=conf, inputs=inputs, group_names=group_names)
    display(ui)
    page_session.wait_for_timeout(1000)
    return ui


def row_by_label(page_session, label: str):
    """
    Locate the row/container element corresponding to a labeled field.

    """
    return page_session.locator(f"text={label}").locator("..")


def set_text_input(
    row,
    *,
    value: Optional[str] = None,
    clear: bool = False,
    text_to_type: Optional[str] = None,
):
    """
    Update a text input located inside a given row.
    """
    inp = row.locator("input")
    if clear:
        inp.clear()
    if value is not None:
        inp.fill(value)
    if text_to_type is not None:
        inp.type(text_to_type)


def test_generic_config_ui_load(
    solara_test,
    page_session,
    assert_solara_snapshot,
    tmp_path,
    inputs_and_groups,
    secrets,
):
    inputs, group_names = inputs_and_groups
    render_ui(page_session, secrets, inputs, group_names)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_icon_on_value_change_by_textfield(
    solara_test,
    page_session,
    assert_solara_snapshot,
    tmp_path,
    inputs_and_groups,
    secrets,
):
    inputs, group_names = inputs_and_groups
    render_ui(page_session, secrets, inputs, group_names)
    fill_text(page_session, "Connection", "Host", "namelocalhost")
    fill_text(page_session, "Credentials", "User", "user")
    save_button(page_session).focus()
    expect_save_button_to_have_pencil_icon(page_session, 1)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_icon_on_value_change_by_checkbox(
    solara_test,
    page_session,
    assert_solara_snapshot,
    tmp_path,
    inputs_and_groups,
    secrets,
):
    inputs, group_names = inputs_and_groups
    render_ui(page_session, secrets, inputs, group_names)
    set_checkbox(page_session, "Encryption", "Encrypted Comm.", checked=True)
    expect_save_button_to_have_pencil_icon(page_session, 1)

    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_empty_checkbox_save(
    solara_test,
    page_session,
    assert_solara_snapshot,
    tmp_path,
    inputs_and_groups,
    secrets,
):
    inputs, group_names = inputs_and_groups
    render_ui(page_session, secrets, inputs, group_names)
    click_save(page_session)

    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_empty_textfield_save(
    solara_test,
    page_session,
    assert_solara_snapshot,
    tmp_path,
    inputs_and_groups,
    secrets,
):
    inputs, group_names = inputs_and_groups
    render_ui(page_session, secrets, inputs, group_names)
    fill_text(page_session, "Connection", "Host", "")
    fill_text(page_session, "Credentials", "User", "")
    set_checkbox(page_session, "Encryption", "Encrypted Comm.", checked=True)
    expect_save_button_to_have_pencil_icon(page_session, 1)
    click_save(page_session)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_for_scs_read_after_save(
    solara_test,
    page_session,
    assert_solara_snapshot,
    tmp_path,
    inputs_and_groups,
    secrets,
):
    inputs, group_names = inputs_and_groups
    render_ui(page_session, secrets, inputs, group_names)
    set_checkbox(page_session, "Encryption", "Encrypted Comm.", checked=True)
    expect_save_button_to_have_pencil_icon(page_session, 1)
    click_save(page_session)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )
    expected_key_values = {
        "db_host_name": "localhost",
        "db_port": "8563",
        "db_user": "sys",
        "db_encryption": "True",
    }
    actual_key_values = dict(secrets.items())
    assert expected_key_values == actual_key_values
