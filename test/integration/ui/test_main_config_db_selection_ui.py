from test.integration.ui.utils.main_config_ui_utils import render_db_selection_ui
from test.integration.ui.utils.ui_utils import (
    SELECT_BUTTON,
    assert_ui_screenshot,
    click_select,
    expect_select_button_to_have_check_icon,
    expect_select_button_to_have_pencil_icon,
)

import pytest


def test_default_db_selection_ui_load(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_db_selection_ui(page_session, secrets)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SELECT_BUTTON,
        parent_levels=1,
    )


@pytest.mark.parametrize(
    "radio_text",
    ["Exasol On-Prem Database", "Exasol SaaS Database"],
)
def test_pencil_icon_radio_select(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets, radio_text
):
    render_db_selection_ui(page_session, secrets)
    page_session.get_by_text(radio_text, exact=True).click()
    expect_select_button_to_have_pencil_icon(page_session)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SELECT_BUTTON,
        parent_levels=1,
    )


def test_check_icon_on_clicking_select(
    solara_test, page_session, assert_solara_snapshot, tmp_path, secrets
):
    render_db_selection_ui(page_session, secrets)
    click_select(page_session)
    expect_select_button_to_have_check_icon(page_session)
    assert_ui_screenshot(
        assert_solara_snapshot,
        page_session,
        anchor_selector=SELECT_BUTTON,
        parent_levels=1,
    )
