from __future__ import annotations

import contextlib
import logging
import os
import re
import shutil
from collections import namedtuple
from enum import (
    Enum,
    auto,
)
from pathlib import Path
from typing import (
    List,
    Optional,
)

from exasol.slc import api as exaslct_api  # type: ignore
from exasol_integration_test_docker_environment.lib.docker import (
    ContextDockerClient,  # type: ignore
)
from git import Repo

from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.language_container_activation import ACTIVATION_KEY_PREFIX
from exasol.nb_connector.secret_store import Secrets

DEFAULT_ALIAS = "ai_lab_default"
PATH_IN_BUCKET = "container"

# Activation SQL for the Custom SLC will be saved in the secret
# store with this key.
SLC_ACTIVATION_KEY_PREFIX = ACTIVATION_KEY_PREFIX + "slc_"

# Path to flavors within the script-languages-release repository
FLAVORS_PATH_IN_SLC_REPO = Path("flavors")

PipPackageDefinition = namedtuple("PipPackageDefinition", ["pkg", "version"])

# Using the SLC_RELEASE 9.6.0 because we are limited to slc-tool 3.*. (see pyproject.toml)
# Check the developer guide (./doc/developer-guide.md) for more information.
SLC_RELEASE_TAG = "9.6.0"


# Maybe we could find a better name for this class?
#
# E.g.
# - SlcCoordinates
# - SlcMetadata
# - SlcLocation
class SlcDir:

    def __init__(self, flavor_name: str, root_dir: Path):
        self.flavor_name = flavor_name
        self.root_dir = root_dir

    @property
    def flavor_path_in_slc_repo(self) -> Path:
        """
        Path to the used flavor within the script-languages-release
        repository
        """
        return FLAVORS_PATH_IN_SLC_REPO / self.flavor_name

    @property
    def flavor_dir(self) -> Path:
        return self.root_dir / self.flavor_path_in_slc_repo

    @property
    def custom_pip_file(self) -> Path:
        """
        Returns the path to the custom pip file of the flavor
        """
        return (
            self.flavor_dir
            / "flavor_customization"
            / "packages"
            / "python3_pip_packages"
        )

    @contextlib.contextmanager
    def enter(self):
        """Changes working directory and returns to previous on exit."""
        prev_cwd = Path.cwd()
        os.chdir(self.root_dir)
        try:
            yield
        finally:
            os.chdir(prev_cwd)

    def __str__(self):
        return str(self.root_dir)

    @classmethod
    def from_secrets(cls, secrets: Secrets, slc_session: SlcSession) -> SlcDir:
        key = slc_session.value
        try:
            flavor_name = secrets[key]
        except AttributeError as ex:
            raise SlctManagerError(
                f"Secret store does not contain an SLC flavor for session {key}"
            ) from ex

        try:
            root_dir = secrets[AILabConfig.slc_target_dir]
        except AttributeError as ex:
            raise SlctManagerError(
                f"Secret store does not contain an SLC target directory"
            )
        return cls(flavor_name, Path(root_dir))


class WorkingDir:
    def __init__(self, p: Path | None):
        if p is None:
            self.root_dir = Path.cwd()
        else:
            self.root_dir = p

    @property
    def export_path(self):
        """
        Returns the export path for script-languages-container
        """
        return self.root_dir / "container"

    @property
    def output_path(self):
        """
        Returns the output path containing caches and logs.
        """
        return self.root_dir / "output"

    def cleanup_output_path(self):
        """
        Remove the output path recursively.
        """
        shutil.rmtree(self.output_path)

    def cleanup_export_path(self):
        """
        Remove the export path recursively
        """
        shutil.rmtree(self.export_path)


class SlcSession(Enum):
    CUDA = CKey.slc_flavor_cuda
    NON_CUDA = CKey.slc_flavor_non_cuda


class SlctManagerError(Exception):
    """
    In case the Secure Configuration Storage (SCS / secrets / conf)
    does not contain specific data required for using the SlctManager.

    E.g. the flavor for the specified SLC session or the SLC target directory.
    """


class SlctManager:
    """
    Support building different flavors of Exasol Script Language
    Containers (SLCs) using the SLCT.

    * The name of the SLC flavor must be provided in secrets

    * Additionally slc_session must specify the key for retrieving
      the flavor name from the SCS

    The caller needs ensure the flavor name is stored in the Secure
    Configuration Storage (SCS / secrets / conf) using the keys
    AILabConfig.slc_flavor_cuda and AILabConfig.slc_flavor_non_cuda.
    Otherwise SlctManager will raise an SlcFlavorNotFoundError.
    """

    def __init__(
        self,
        secrets: Secrets,
        working_path: Path | None = None,
        slc_session: SlcSession = SlcSession.NON_CUDA,
    ):
        self._secrets = secrets
        self.working_path = WorkingDir(working_path)
        self.slc_dir = SlcDir.from_secrets(secrets, slc_session)

    def check_slc_repo_complete(self) -> bool:
        """
        Checks if the target dir for the script-languages repository is present and correct.
        """
        print(f"Script-languages repository path is '{self.slc_dir}'")
        if not self.slc_dir.flavor_dir.is_dir():
            return False
        return True

    def clone_slc_repo(self):
        """
        Clones the script-languages-release repository from Github into
        the target dir configured in the secret store.
        """
        if not self.slc_dir.root_dir.is_dir():
            logging.info(f"Cloning into {self.slc_dir}...")
            repo = Repo.clone_from(
                "https://github.com/exasol/script-languages-release",
                self.slc_dir.root_dir,
                branch=SLC_RELEASE_TAG,
            )
            logging.info("Fetching submodules...")
            repo.submodule_update(recursive=True)
        else:
            logging.warning(
                f"Directory '{self.slc_dir}' already exists. Skipping cloning...."
            )

    @property
    def flavor_path(self) -> str:
        return str(self.slc_dir.flavor_path_in_slc_repo)

    def export(self):
        """
        Exports the current script-languages-container to the export directory.
        """
        with self.slc_dir.enter():
            exaslct_api.export(
                flavor_path=tuple(self.flavor_path),
                export_path=str(self.working_path.export_path),
                output_directory=str(self.working_path.output_path),
                release_name=self.language_alias,
            )

    def upload(self):
        """
        Uploads the current script-languages-container to the database
        and stores the activation string in the secret store.
        """
        bucketfs_name = self._secrets.get(CKey.bfs_service)
        bucket_name = self._secrets.get(CKey.bfs_bucket)
        database_host = self._secrets.get(CKey.bfs_host_name)
        bucketfs_port = self._secrets.get(CKey.bfs_port)
        bucketfs_username = self._secrets.get(CKey.bfs_user)
        bucketfs_password = self._secrets.get(CKey.bfs_password)

        with self.slc_dir.enter():
            exaslct_api.upload(
                flavor_path=tuple(self.flavor_path),
                database_host=database_host,
                bucketfs_name=bucketfs_name,
                bucket_name=bucket_name,
                bucketfs_port=int(bucketfs_port),
                bucketfs_username=bucketfs_username,
                bucketfs_password=bucketfs_password,
                path_in_bucket=PATH_IN_BUCKET,
                release_name=self.language_alias,
                output_directory=str(self.working_path.output_path),
            )
            container_name = f"{self.slc_dir.flavor_name}-release-{self.language_alias}"
            result = exaslct_api.generate_language_activation(
                flavor_path=self.flavor_path,
                bucketfs_name=bucketfs_name,
                bucket_name=bucket_name,
                container_name=container_name,
                path_in_bucket=PATH_IN_BUCKET,
            )

            alter_session_cmd = result[0]
            re_res = re.search(
                r"ALTER SESSION SET SCRIPT_LANGUAGES='(.*)'", alter_session_cmd
            )
            activation_key = re_res.groups()[0]
            _, url = activation_key.split("=", maxsplit=1)
            self._secrets.save(self._alias_key, f"{self.language_alias}={url}")

    @property
    def _alias_key(self):
        return SLC_ACTIVATION_KEY_PREFIX + self.language_alias

    @property
    def activation_key(self) -> str:
        """
        Returns the language activation string for the uploaded script-language-container.
        Can be used in `ALTER SESSION` or `ALTER_SYSTEM` SQL commands to activate
        the language of the uploaded script-language-container.
        """
        activation_key = self._secrets.get(self._alias_key)
        if not activation_key:
            raise RuntimeError("SLC activation key not defined in secrets.")
        return activation_key

    @property
    def language_alias(self) -> str:
        """
        Returns the stored language alias.
        """
        language_alias = self._secrets.get(AILabConfig.slc_alias, DEFAULT_ALIAS)
        if not language_alias:
            return DEFAULT_ALIAS
        return language_alias

    @language_alias.setter
    def language_alias(self, alias: str):
        """
        Stores the language alias in the secret store.
        """
        self._secrets.save(AILabConfig.slc_alias, alias)

    def append_custom_packages(self, pip_packages: list[PipPackageDefinition]):
        """
        Appends packages to the custom pip file.

        Note: This method is not idempotent: Multiple calls with the same
        package definitions will result in duplicated entries.
        """
        with open(self.slc_dir.custom_pip_file, "a") as f:
            for p in pip_packages:
                print(f"{p.pkg}|{p.version}", file=f)

    @property
    def slc_docker_images(self):
        with ContextDockerClient() as docker_client:
            images = docker_client.images.list(name="exasol/script-language-container")
            image_tags = [img.tags[0] for img in images]
            return image_tags

    def clean_all_images(self):
        """
        Deletes all local docker images.
        """
        exaslct_api.clean_all_images(
            output_directory=str(self.working_path.output_path)
        )
