from test.integration.ui.utils.main_config_ui_utils import render_onprem_non_itde_ui
from test.integration.ui.utils.ui_utils import (
    SAVE_BUTTON,
    assert_ui_screenshot,
    click_save,
    expect_save_button_to_have_check_icon,
    expect_save_button_to_have_pencil_icon,
    fill_text,
    save_button,
    set_checkbox,
)


def test_external_port_bring_original_value(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_onprem_non_itde_ui(page_session, secrets)
    fill_text(page_session, "BucketFS Connection", "External Port", "")
    save_button(page_session).focus()
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_internal_port_bring_original_value(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_onprem_non_itde_ui(page_session, secrets)
    fill_text(page_session, "BucketFS Connection", "Internal Port", "")
    save_button(page_session).focus()
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_pencil_icon_on_textfield_change(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_onprem_non_itde_ui(page_session, secrets)
    fill_text(page_session, "BucketFS Connection", "User Name", "bfs_test_system")
    expect_save_button_to_have_pencil_icon(page_session, 1)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_pencil_icon_on_checkbox_change(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_onprem_non_itde_ui(page_session, secrets)
    set_checkbox(page_session, "BucketFS Connection", "Encrypted Comm.", checked=False)
    expect_save_button_to_have_pencil_icon(page_session, 1)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


def test_check_icon_on_save(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_onprem_non_itde_ui(page_session, secrets)
    fill_text(page_session, "BucketFS Connection", "User Name", "bfs_test_system")
    set_checkbox(page_session, "BucketFS Connection", "Encrypted Comm.", checked=False)
    expect_save_button_to_have_pencil_icon(page_session, 1)
    click_save(page_session)
    expect_save_button_to_have_check_icon(page_session, 1)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )
