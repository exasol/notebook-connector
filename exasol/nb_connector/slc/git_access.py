import abc
import logging
from pathlib import Path

from git import Repo

from exasol.nb_connector.slc import constants

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


class GitAccessIf(abc.ABC):
    @abc.abstractmethod
    def clone_from_recursively(self, url: str, path: Path, branch: str) -> None:
        pass

    @abc.abstractmethod
    def checkout_recursively(self, path: Path) -> None:
        pass


class GitAccess(GitAccessIf):
    def clone_from_recursively(self, url: str, path: Path, branch: str) -> None:
        LOG.info(f"Cloning into {path}...")
        repo = Repo.clone_from(
            constants.SLC_GITHUB_REPO,
            path,
            branch=branch,
        )
        LOG.info("Fetching submodules...")
        repo.submodule_update(recursive=True)

    def checkout_recursively(self, path: Path) -> None:
        repo = Repo(path)
        repo.git.checkout("--recurse-submodules", ".")
