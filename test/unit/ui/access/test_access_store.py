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
    monkeypatch.delenv("NOTEBOOK_DIR", raising=False)

    if test_scs_file.exists():
        test_scs_file.unlink()

    assert access_ui.get_sb_store_file() == access_ui.DEFAULT_FILE_NAME
    ui = access_ui.get_access_store()
    assert ui.children[0].children[1].children[1].value == access_ui.DEFAULT_FILE_NAME
    absolute_file_path = str((tmp_path / TEST_CONFIG_SQLITE).resolve())
    file_name_field = ui.children[0].children[1].children[1]
    file_name_field.value = absolute_file_path
    password_field = ui.children[0].children[2].children[1]
    password_field.value = "password"
    open_button = ui.children[1]
    open_button.click()
    assert test_scs_file.read_text().strip() == absolute_file_path
    assert access_ui.get_sb_store_file() == absolute_file_path
    assert file_name_field.value == TEST_CONFIG_SQLITE

    ui_read = access_ui.get_access_store()
    stored_name_field = ui_read.children[0].children[1].children[1]
    assert stored_name_field.value == TEST_CONFIG_SQLITE


def test_access_store_legacy_relative_path_is_upgraded_to_absolute(
    tmp_path, monkeypatch
):
    """
    Test that a legacy relative cache entry is resolved against NOTEBOOK_DIR and
    rewritten in absolute form after the store is opened.
    """
    monkeypatch.chdir(tmp_path)
    test_scs_file = tmp_path / "scs_file"
    monkeypatch.setattr(access_ui, "get_scs_location_file_path", lambda: test_scs_file)
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path))

    legacy_relative_path = "legacy_config.sqlite"
    test_scs_file.write_text(legacy_relative_path)

    ui = access_ui.get_access_store()
    file_name_field = ui.children[0].children[1].children[1]
    expected_absolute_path = str((tmp_path / legacy_relative_path).resolve())
    assert file_name_field.value == legacy_relative_path

    password_field = ui.children[0].children[2].children[1]
    password_field.value = "password"
    open_button = ui.children[1]
    open_button.click()

    assert test_scs_file.read_text().strip() == expected_absolute_path
    assert access_ui.get_sb_store_file() == expected_absolute_path
    assert file_name_field.value == legacy_relative_path


def test_access_store_explicit_root_dir_overrides_notebook_dir(
    tmp_path, monkeypatch
):
    """
    Test that an explicit root_dir is preferred over NOTEBOOK_DIR for display and
    resolution.
    """
    monkeypatch.chdir(tmp_path)
    test_scs_file = tmp_path / "scs_file"
    monkeypatch.setattr(access_ui, "get_scs_location_file_path", lambda: test_scs_file)
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path / "notebook"))

    explicit_root_dir = tmp_path / "explicit-root"
    explicit_root_dir.mkdir()
    relative_file_path = "explicit.sqlite"
    test_scs_file.write_text(relative_file_path)

    ui = access_ui.get_access_store(str(explicit_root_dir))
    file_name_field = ui.children[0].children[1].children[1]
    expected_absolute_path = str((explicit_root_dir / relative_file_path).resolve())
    assert file_name_field.value == relative_file_path

    password_field = ui.children[0].children[2].children[1]
    password_field.value = "password"
    open_button = ui.children[1]
    open_button.click()

    assert test_scs_file.read_text().strip() == expected_absolute_path
    assert access_ui.get_sb_store_file() == expected_absolute_path
    assert file_name_field.value == relative_file_path


def test_access_store_absolute_path_outside_base_is_displayed_absolute(
    tmp_path, monkeypatch
):
    """
    Test that an absolute path outside the base directory stays absolute in the UI.
    """
    monkeypatch.chdir(tmp_path)
    test_scs_file = tmp_path / "scs_file"
    monkeypatch.setattr(access_ui, "get_scs_location_file_path", lambda: test_scs_file)
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path / "notebook"))

    outside_path = (tmp_path / "outside" / TEST_CONFIG_SQLITE).resolve()
    outside_path.parent.mkdir()
    test_scs_file.write_text(str(outside_path))

    ui = access_ui.get_access_store()
    file_name_field = ui.children[0].children[1].children[1]
    assert file_name_field.value == str(outside_path)


def test_access_store_relative_input_falls_back_to_cwd(
    tmp_path, monkeypatch
):
    """
    Test that relative input resolves against the current working directory when
    neither root_dir nor NOTEBOOK_DIR is available.
    """
    monkeypatch.chdir(tmp_path)
    test_scs_file = tmp_path / "scs_file"
    monkeypatch.setattr(access_ui, "get_scs_location_file_path", lambda: test_scs_file)
    monkeypatch.delenv("NOTEBOOK_DIR", raising=False)

    ui = access_ui.get_access_store()
    file_name_field = ui.children[0].children[1].children[1]
    relative_file_path = "cwd_relative.sqlite"
    file_name_field.value = relative_file_path

    password_field = ui.children[0].children[2].children[1]
    password_field.value = "password"
    open_button = ui.children[1]
    open_button.click()

    expected_absolute_path = str((tmp_path / relative_file_path).resolve())
    assert file_name_field.value == relative_file_path
    assert test_scs_file.read_text().strip() == expected_absolute_path
    assert access_ui.get_sb_store_file() == expected_absolute_path


def test_access_store_relative_input_is_resolved_against_notebook_dir(
    tmp_path, monkeypatch
):
    """
    Test that a relative file path entered in the UI is resolved against
    NOTEBOOK_DIR and stored as an absolute path.
    """
    monkeypatch.chdir(tmp_path)
    test_scs_file = tmp_path / "scs_file"
    monkeypatch.setattr(access_ui, "get_scs_location_file_path", lambda: test_scs_file)
    monkeypatch.setenv("NOTEBOOK_DIR", str(tmp_path))

    ui = access_ui.get_access_store()
    file_name_field = ui.children[0].children[1].children[1]
    relative_file_path = "entered_relative.sqlite"
    file_name_field.value = relative_file_path

    password_field = ui.children[0].children[2].children[1]
    password_field.value = "password"
    open_button = ui.children[1]
    open_button.click()

    expected_absolute_path = str((tmp_path / relative_file_path).resolve())
    assert file_name_field.value == relative_file_path
    assert test_scs_file.read_text().strip() == expected_absolute_path
    assert access_ui.get_sb_store_file() == expected_absolute_path
