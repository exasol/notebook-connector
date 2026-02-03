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