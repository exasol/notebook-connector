from pathlib import Path

from exasol.toolbox.config import BaseConfig

PROJECT_CONFIG = BaseConfig(
    root_path=Path(__file__).parent,
    project_name="nb_connector",
    # currently only python 3.10 is supported due to
    # dependencies on binary provision such as TXAIE
    python_versions=("3.10",),
    add_to_excluded_python_paths=("ui_snapshots",),
)
