"""
Unit tests for access store read and write functions.
"""

import exasol.nb_connector.ui.access_store_ui as access_ui


def test_access_store_ui_store_read_and_write_2(tmp_path, monkeypatch):
    """
    Test access store UI reading and writing SCS file path via widgets
    and helper functions.
    """
    monkeypatch.chdir(tmp_path)
    test_scs_file = tmp_path / "scs_file"
    monkeypatch.setattr(access_ui, "get_scs_location_file_path", lambda: test_scs_file)

    if test_scs_file.exists():
        test_scs_file.unlink()

    assert access_ui.get_sb_store_file() == access_ui.DEFAULT_FILE_NAME
    # open UI
    ui = access_ui.get_access_store_ui(str(tmp_path))
    # select the textfield and enter file name
    file_name = ui.children[0].children[1].children[1]
    file_name.value = "test_config.sqlite"
    # select the password field and enter password
    password = ui.children[0].children[2].children[1]
    password.value = "password"
    # click the open button
    open_button = ui.children[1]
    open_button.click()
    # assert the file name
    assert test_scs_file.read_text().strip() == "test_config.sqlite"
    assert access_ui.get_sb_store_file() == "test_config.sqlite"
