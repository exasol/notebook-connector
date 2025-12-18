"""
Test module for access_store_ui_app.py
"""

import importlib
import shutil
import subprocess
from pathlib import Path

from exasol.nb_connector.ui import access_store_ui


def _remove_global_store():
    """Delete the global cache file for store between tests."""
    store_file = Path.home() / ".cache" / "notebook-connector" / "scs_file"
    if store_file.exists():
        store_file.unlink()


def test_store_file_write(tmp_path, monkeypatch):
    """
    Test for store file write functionality using the real ~/.cache file.
    """
    # Clean before test
    _remove_global_store()

    # Copy the app file into tmp_path
    source_app = importlib.resources.files("test.unit.ui") / "access_store_ui_app.py"
    target_app = tmp_path / "access_store_ui_app.py"
    shutil.copyfile(source_app, target_app)
    script_file = target_app

    monkeypatch.chdir(tmp_path)

    command = ["ipython", script_file]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        print("--- Subprocess Output (stdout) ---")
        print(result.stdout)
        print("--- Subprocess Errors (stderr) ---")
        print(result.stderr)
        print(f"Subprocess finished with return code: {result.returncode}")

        # checking if the file is created
        # checking if the file has expected value
        store_file = Path.home() / ".cache" / "notebook-connector" / "scs_file"
        assert store_file.exists()
        assert store_file.read_text().strip() == access_store_ui.DEFAULT_FILE_NAME
    except subprocess.CalledProcessError as e:
        print(f"Error executing IPython script: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        assert False
    except FileNotFoundError:
        print("Error: The 'ipython' command was not found. Check your PATH.")
        assert False
    finally:
        # safely delete after test
        _remove_global_store()
