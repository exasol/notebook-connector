import logging
from pathlib import Path

from git import Repo

from exasol.nb_connector.slc import constants

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


class GitAccess:
    @staticmethod
    def clone_from_recursively(url: str, path: Path, branch: str) -> None:
        LOG.info(f"Cloning into {path}...")
        repo = Repo.clone_from(
            constants.SLC_GITHUB_REPO,
            path,
            branch=branch,
        )
        LOG.info("Fetching submodules...")
        repo.submodule_update(recursive=True)

    @staticmethod
    def checkout_recursively(path: Path) -> None:
        repo = Repo(path)
        repo.git.checkout("--recurse-submodules", ".")

    @staticmethod
    def checkout_file(repo_path: Path, file: Path) -> None:
        repo = Repo(repo_path)
        repo.git.checkout("HEAD", "--", str(file))
