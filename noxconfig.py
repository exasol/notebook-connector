from pathlib import Path

from exasol.toolbox.config import BaseConfig

PROJECT_CONFIG = BaseConfig(
    root_path=Path(__file__).parent,
    project_name="nb_connector",
    # currently only python 3.13 is not supported due to
    # our dependencies do not support 3.13 yet.
    # ticket ca be found here: https://github.com/exasol/notebook-connector/issues/471
    python_versions=(
        "3.10",
        "3.11",
        "3.12",
    ),
    add_to_excluded_python_paths=("ui_snapshots", "test-results", ".venv-1", ".venv"),
)
