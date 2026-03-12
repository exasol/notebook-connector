"""
Unit tests for access store read and write functions.
"""

import exasol.nb_connector.ui.access.access_store as access_ui

TEST_CONFIG_SQLITE = "test_config.sqlite"


def test_access_store_ui_store_read_and_write(tmp_path, monkeypatch):
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
    ui = access_ui.get_access_store(str(tmp_path))
    absolute_file_path = str((tmp_path / TEST_CONFIG_SQLITE).resolve())
    file_name_field = ui.children[0].children[1].children[1]
    file_name_field.value = absolute_file_path
    password_field = ui.children[0].children[2].children[1]
    password_field.value = "password"
    open_button = ui.children[1]
    open_button.click()
    assert test_scs_file.read_text().strip() == absolute_file_path
    assert access_ui.get_sb_store_file() == absolute_file_path

    ui_read = access_ui.get_access_store(str(tmp_path))
    stored_name_field = ui_read.children[0].children[1].children[1]
    assert stored_name_field.value == absolute_file_path
