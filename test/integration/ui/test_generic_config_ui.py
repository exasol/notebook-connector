from test.integration.ui.ui_utils import assert_ui_screenshot

import ipywidgets as widgets
import pytest
from IPython.display import display
from playwright.sync_api import expect

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
    return Secrets(db_file=scs_file, master_password="password")


def render_ui(page_session, conf, inputs, group_names):
    """
    Render the generic config UI
    """
    ui = get_generic_config_ui(conf=conf, inputs=inputs, group_names=group_names)
    display(ui)
    page_session.wait_for_timeout(1000)
    return ui


def row_by_label(page_session, label: str):
    """
    Locate the row/container element corresponding to a labeled field.

    """
    return page_session.locator(f"text={label}").locator("..")


def set_text_input(
    row, *, value: str = None, clear: bool = False, text_to_type: str = None
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


def checkbox(page_session):
    """
    Locate the checkbox input in the current UI. We have only one for now.
    """
    return page_session.locator("input[type='checkbox']")


def click_save(page_session):
    """
    Click the 'Save' button in the UI.
    """
    page_session.locator("button:text('Save')").click()


def save_button(page_session):
    """
    Locate the 'Save' button.
    """
    return page_session.locator("button:text('Save')")


def expect_check_icon(page_session, count: int = 1):
    """
    Assert the presence/absence count of the 'pen' icon inside the Save button.
    """
    expect(save_button(page_session).locator("i.fa-check")).to_have_count(count)


def expect_pen_icon(page_session, count: int = 1):
    """
    Assert the presence/absence count of the 'pen' icon inside the Save button.
    """
    expect(save_button(page_session).locator("i.fa-pen")).to_have_count(count)


def assert_screenshot(assert_solara_snapshot, page_session):
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector="button:text('Save')",
        parent_levels=1,  # button -> parent
    )


def change_host_and_user(page_session):
    """
    Fill the  fields for saving a config.
    """
    set_text_input(row_by_label(page_session, "Host"), text_to_type="name")
    set_text_input(row_by_label(page_session, "User"), value="user")


def test_generic_config_ui_load(
    solara_test, page_session, assert_solara_snapshot, tmp_path, inputs_and_groups
):
    conf = create_conf(tmp_path)
    inputs, group_names = inputs_and_groups
    render_ui(page_session, conf, inputs, group_names)
    assert_screenshot(assert_solara_snapshot, page_session)


def test_icon_on_value_change_by_textfield(
    solara_test, page_session, assert_solara_snapshot, tmp_path, inputs_and_groups
):
    conf = create_conf(tmp_path)
    inputs, group_names = inputs_and_groups
    render_ui(page_session, conf, inputs, group_names)

    change_host_and_user(page_session)
    expect_pen_icon(page_session, 1)

    assert_screenshot(assert_solara_snapshot, page_session)


def test_icon_on_value_change_by_checkbox(
    solara_test, page_session, assert_solara_snapshot, tmp_path, inputs_and_groups
):
    conf = create_conf(tmp_path)
    inputs, group_names = inputs_and_groups
    render_ui(page_session, conf, inputs, group_names)

    checkbox(page_session).set_checked(True)
    expect_pen_icon(page_session, 1)

    assert_screenshot(assert_solara_snapshot, page_session)


def test_empty_checkbox_save(
    solara_test, page_session, assert_solara_snapshot, tmp_path, inputs_and_groups
):
    conf = create_conf(tmp_path)
    inputs, group_names = inputs_and_groups
    render_ui(page_session, conf, inputs, group_names)
    click_save(page_session)

    assert_screenshot(assert_solara_snapshot, page_session)


def test_empty_textfield_save(
    solara_test, page_session, assert_solara_snapshot, tmp_path, inputs_and_groups
):
    conf = create_conf(tmp_path)
    inputs, group_names = inputs_and_groups
    render_ui(page_session, conf, inputs, group_names)

    set_text_input(row_by_label(page_session, "Host"), clear=True)
    set_text_input(row_by_label(page_session, "User"), clear=True)
    checkbox(page_session).set_checked(True)
    expect_pen_icon(page_session, 1)
    click_save(page_session)
    assert_screenshot(assert_solara_snapshot, page_session)


def test_for_scs_read_after_save(
    solara_test, page_session, assert_solara_snapshot, tmp_path, inputs_and_groups
):
    conf = create_conf(tmp_path)
    inputs, group_names = inputs_and_groups
    render_ui(page_session, conf, inputs, group_names)
    checkbox(page_session).set_checked(True)
    expect_pen_icon(page_session, 1)
    assert_screenshot(assert_solara_snapshot, page_session)
    click_save(page_session)
    print(list(tmp_path.iterdir()))
    print("#" * 100)
    scs_file = tmp_path / "sample_scs_file.sqlite"
    assert scs_file.exists()
    assert not list(Secrets(scs_file, "password").keys())
