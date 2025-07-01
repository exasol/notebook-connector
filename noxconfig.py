from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).parent


@dataclass(frozen=True)
class Config:
    root: Path = ROOT_DIR
    doc: Path = ROOT_DIR / "doc"
    version_file: Path = ROOT_DIR / "version.py"
    path_filters: Iterable[str] = ("dist", ".eggs", "venv")
    python_versions = ["3.10", "3.11", "3.12"]


PROJECT_CONFIG = Config()
