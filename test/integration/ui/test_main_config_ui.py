from pathlib import Path
from typing import Optional

from IPython.display import display
from playwright.sync_api import expect

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.ui.main_config_ui import get_db_config_ui, get_db_selection_ui
from test.integration.ui.ui_utils import assert_ui_screenshot

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey, StorageBackend


def create_conf(tmp_path):
    """
    Create a Secret configuration store using a temporary SQLite file.
    """
    scs_file = str(tmp_path / "sample_scs_file.sqlite")
    return Secrets(db_file=Path(scs_file), master_password="password")


def render_main_config_ui(page_session, conf):
    """
    Render the main config UI
    """
    ui = get_db_config_ui(conf=conf)
    display(ui)
    page_session.wait_for_timeout(1000)
    return ui


def render_db_selection_ui(page_session, conf):
    ui = get_db_selection_ui(conf=conf)
    display(ui)
    page_session.wait_for_timeout(1000)
    return ui


def assert_config_ui_screenshot(assert_solara_snapshot, page_session):
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector="button:text('Save')",
        parent_levels=1,
    )


def assert_selection_ui_screenshot(assert_solara_snapshot, page_session):
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector="button:text('Select')",
        parent_levels=1,
    )


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


def row_by_label(page_session, label: str):
    """
    Locate the row/container element corresponding to a labeled field.

    """
    return page_session.locator(f"text={label}").locator("..")


def save_button(page_session):
    """
    Locate the 'Save' button.
    """
    return page_session.locator("button:text('Save')")


def click_save(page_session):
    """
    Click the 'Save' button in the UI.
    """
    page_session.locator("button:text('Save')").click()
    print("clicked Save button")


def expect_pen_icon(page_session, count: int = 1):
    """
    Assert the presence/absence count of the 'pen' icon inside the Save button.
    """
    expect(save_button(page_session).locator("i.fa-pen")).to_have_count(count)


def expect_check_icon(page_session, count: int = 1):
    """
    Assert the presence/absence count of the 'pen' icon inside the Save button.
    """
    expect(save_button(page_session).locator("i.fa-check")).to_have_count(count)


def test_default_main_config_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    render_main_config_ui(page_session, conf)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)


def test_default_main_config_load_default_on_clear(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    render_main_config_ui(page_session, conf)
    set_text_input(row_by_label(page_session, "Memory Size (GiB)"), clear=True)
    set_text_input(row_by_label(page_session, "Disk Size (GiB)"), clear=True)
    save_button(page_session).focus()
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)


def test_default_main_config_pen_icon_on_change(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    render_main_config_ui(page_session, conf)
    set_text_input(row_by_label(page_session, "Memory Size (GiB)"), text_to_type="4")
    page_session.locator("button:text('Save')").focus()
    expect_pen_icon(page_session, 1)
    page_session.get_by_role("button", name="Please Save").focus()
    page_session.locator("button:text('Please Save')").focus()
    # TODO: cannot see pen icon in the screenshot, need to find a solution for that
    page_session.wait_for_timeout(3000)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)


def test_default_main_config_check_icon_on_save(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    render_main_config_ui(page_session, conf)
    set_text_input(row_by_label(page_session, "Memory Size (GiB)"), value="3")
    click_save(page_session)
    page_session.wait_for_timeout(5000)
    expect_check_icon(page_session, 1)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)


def test_default_main_config_check_icon_on_save_direct(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = Secrets(db_file=Path(tmp_path / "sample.sqlite"), master_password="password")
    render_main_config_ui(page_session, conf)
    set_text_input(row_by_label(page_session, "Memory Size (GiB)"), value="3")
    page_session.locator("button:text('Save')").click()
    expect_check_icon(page_session, 1)


def test_onprem_main_config_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    conf.save(CKey.storage_backend, StorageBackend.onprem.name)
    render_main_config_ui(page_session, conf)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)


def test_saas_main_config_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    conf.save(CKey.storage_backend, StorageBackend.saas.name)
    render_main_config_ui(page_session, conf)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)


def test_saas_ui_pen_on_change(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    conf.save(CKey.storage_backend, StorageBackend.saas.name)
    render_main_config_ui(page_session, conf)
    set_text_input(row_by_label(page_session, "Account ID"), value="account_id")
    set_text_input(row_by_label(page_session, "Database ID"), value="database_id")
    expect_pen_icon(page_session, 1)
    """
    TODO: cannot see pen icon in the screenshot, 
    but playwright is able detect the icon in the above line of code 
    `expect_pen_icon(page_session, 1)`
    need to find a solution for that and enable screenshot asserion
    """
    # assert_config_ui_screenshot(assert_solara_snapshot, page_session)


def test_saas_ui_check_on_save(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    conf.save(CKey.storage_backend, StorageBackend.saas.name)
    render_main_config_ui(page_session, conf)
    set_text_input(row_by_label(page_session, "Account ID"), value="account_id")
    set_text_input(row_by_label(page_session, "Database ID"), value="database_id")
    expect_pen_icon(page_session, 1)
    click_save(page_session)
    # expect(page_session.get_by_role("button", name="Saved")).to_be_visible()

    assert_config_ui_screenshot(assert_solara_snapshot, page_session)


def test_itde_main_config_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    conf.save(CKey.use_itde, "True")
    render_main_config_ui(page_session, conf)
    assert_config_ui_screenshot(assert_solara_snapshot, page_session)


def test_default_db_selection_ui_load(
        solara_test, page_session, assert_solara_snapshot, tmp_path
):
    conf = create_conf(tmp_path)
    render_db_selection_ui(page_session, conf)
    assert_selection_ui_screenshot(assert_solara_snapshot, page_session)
