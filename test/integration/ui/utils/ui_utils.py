from typing import Optional

from playwright.sync_api import expect

SAVE_BUTTON = "button:text('Save')"
SELECT_BUTTON = "button:text('Select')"
CONF_STORE = ":text('Configuration Store')"


def assert_ui_screenshot(
    assert_solara_snapshot,
    page_session,
    *,
    anchor_selector: str,
    parent_levels: int = 0,
    wait_ms: int = 1000,
):
    """

    Takes a screenshot of a UI part and compares it to the saved one.
        anchor_selector: element to find
        parent_levels: go up .. this many times
        wait_ms: wait before finding
    """
    if wait_ms:
        page_session.wait_for_timeout(wait_ms)

    box = page_session.locator(anchor_selector)
    for _ in range(parent_levels):
        box = box.locator("..")

    box.wait_for()
    assert_solara_snapshot(box.screenshot())


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
    return page_session.locator(SAVE_BUTTON)


def select_button(page_session):
    """
    Locate the 'Save' button.
    """
    return page_session.locator(SELECT_BUTTON)


def click_save(page_session):
    """
    Click the 'Save' button in the UI.
    """
    page_session.locator(SAVE_BUTTON).click()


def click_select(page_session):
    """
    Click the 'Save' button in the UI.
    """
    page_session.locator(SELECT_BUTTON).click()


def expect_save_button_to_have_pencil_icon(page_session, count: int = 1):
    """
    Assert the presence/absence count of the 'pen' icon inside the Save button.
    """
    expect(save_button(page_session).locator("i.fa-pencil")).to_have_count(count)


def expect_select_button_to_have_pencil_icon(page_session, count: int = 1):
    """
    Assert the presence/absence count of the 'pen' icon inside the Save button.
    """
    expect(select_button(page_session).locator("i.fa-pencil")).to_have_count(count)


def expect_save_button_to_have_check_icon(page_session, count: int = 1):
    """
    Assert the presence/absence count of the 'pen' icon inside the Save button.
    """
    expect(save_button(page_session).locator("i.fa-check")).to_have_count(count)


def expect_select_button_to_have_check_icon(page_session, count: int = 1):
    """
    Assert the presence/absence count of the 'pen' icon inside the Select button.
    """
    expect(select_button(page_session).locator("i.fa-check")).to_have_count(count)


def fill_text(
    page_session,
    panel_title: str,
    label_text: str,
    value: str,
    *,
    input_xpath: str = "xpath=following::input[1]",
    exact: bool = True,
) -> None:
    panel = page_session.get_by_text(panel_title, exact=exact).locator("..")
    label = panel.get_by_text(label_text, exact=exact)
    label.locator(input_xpath).fill(value)


def set_checkbox(
    page_session,
    panel_title: str,
    label_text: str,
    checked: bool,
    *,
    checkbox_xpath: str = "xpath=following::input[@type='checkbox'][1]",
    exact: bool = True,
) -> None:
    panel = page_session.get_by_text(panel_title, exact=exact).locator("..")
    label = panel.get_by_text(label_text, exact=exact)
    cb = label.locator(checkbox_xpath)
    cb.check() if checked else cb.uncheck()
