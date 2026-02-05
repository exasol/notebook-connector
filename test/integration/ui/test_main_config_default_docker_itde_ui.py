from test.integration.ui.utils.main_config_ui_utils import (
    assert_main_config_ui_screenshot,
    render_main_config_ui,
)
from test.integration.ui.utils.ui_utils import (
    SAVE_BUTTON,
    assert_ui_screenshot,
    click_save,
    expect_save_button_to_have_check_icon,
    expect_save_button_to_have_pencil_icon,
    fill_text,
    save_button,
)


def test_default_main_config_ui_load(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_main_config_ui(page_session, secrets)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_default_main_config_load_default_on_clear(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_main_config_ui(page_session, secrets)
    fill_text(page_session, "Database Configuration", "Memory Size (GiB)", "")
    fill_text(page_session, "Database Configuration", "Disk Size (GiB)", "")
    save_button(page_session).focus()
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_default_main_config_pencil_icon_on_change(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_main_config_ui(page_session, secrets)
    fill_text(page_session, "Database Configuration", "Memory Size (GiB)", "4")
    save_button(page_session).focus()
    expect_save_button_to_have_pencil_icon(page_session, 1)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_default_main_config_check_icon_on_save(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_main_config_ui(page_session, secrets)
    fill_text(page_session, "Database Configuration", "Memory Size (GiB)", "4")
    fill_text(page_session, "Database Configuration", "Disk Size (GiB)", "4")
    click_save(page_session)
    expect_save_button_to_have_check_icon(page_session, 1)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )
