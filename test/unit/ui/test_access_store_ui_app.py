"""
Test module for access_store_ui_app.py
"""
import importlib
import shutil
import subprocess


def test_store_magic_write(tmp_path, monkeypatch):
    """
    test for store magic write functionality
    """
    # Copy the app file into tmp_path
    source_app = importlib.resources.files("test.unit.ui") / "access_store_ui_app.py"
    target_app = tmp_path / "access_store_ui_app.py"
    shutil.copyfile(source_app, target_app)
    # change current dir to tmp_path
    monkeypatch.chdir(tmp_path)
    # Name of the IPython file to run
    script_file = target_app

    # The command to execute: 'ipython' followed by the script file path
    # Note: On some systems,
    # you might need 'python -m IPython' instead of just 'ipython'
    command = ["ipython", script_file]

    try:
        # Run the command
        result = subprocess.run(
            command,
            capture_output=True,  # Captures stdout and stderr
            text=True,  # Decodes stdout/stderr as text
            # Raises CalledProcessError if the command returns a non-zero exit code
            check=True,
        )

        print("--- Subprocess Output (stdout) ---")
        print(result.stdout)
        print("--- Subprocess Errors (stderr) ---")
        print(result.stderr)
        print(f"Subprocess finished with return code: {result.returncode}")

    except subprocess.CalledProcessError as e:
        print(f"Error executing IPython script: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        assert False
    except FileNotFoundError:
        # This might happen if 'ipython' is not in your system's PATH
        print("Error: The 'ipython' command was not found. Check your PATH.")
        assert False
