from test.integration.ui.utils.main_config_ui_utils import render_saas_ui
from test.integration.ui.utils.ui_utils import (
    SAVE_BUTTON,
    assert_ui_screenshot,
    click_save,
    expect_save_button_to_have_check_icon,
    expect_save_button_to_have_pencil_icon,
    fill_text,
)

import pytest


def test_saas_main_config_ui_load(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_saas_ui(page_session, secrets)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("Account ID", "accountId"),
        ("Database ID", "databaseId"),
        ("Database Name", "databaseName"),
        ("Personal Access Token", "PAT_Access_Token"),
        ("Default Schema", "defaultSchema"),
    ],
)
def test_pencil_icon_on_textfield_change(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets, field, value
):
    render_saas_ui(page_session, secrets)
    fill_text(page_session, "SaaS DB Configuration", field, value)
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
    render_saas_ui(page_session, secrets)

    fill_text(page_session, "SaaS DB Configuration", "Account ID", "accountId")
    fill_text(page_session, "SaaS DB Configuration", "Database ID", "databaseId")
    fill_text(page_session, "SaaS DB Configuration", "Database Name", "databaseName")
    fill_text(
        page_session,
        "SaaS DB Configuration",
        "Personal Access Token",
        "PAT_Access_Token",
    )
    fill_text(page_session, "SaaS DB Configuration", "Default Schema", "defaultSchema")
    expect_save_button_to_have_pencil_icon(page_session, 1)
    click_save(page_session)
    expect_save_button_to_have_check_icon(page_session, 1)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SAVE_BUTTON,
        parent_levels=1,
    )
