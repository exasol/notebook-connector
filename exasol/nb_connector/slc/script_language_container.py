from __future__ import annotations

import contextlib
import logging
import os
import re
import shutil
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from exasol.slc import api as exaslct_api
from exasol_integration_test_docker_environment.lib.docker import (
    ContextDockerClient,
)
from git import Repo

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.language_container_activation import ACTIVATION_KEY_PREFIX
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc import constants
from exasol.nb_connector.slc.slc_flavor import (
    SlcError,
    SlcFlavor,
)

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


PipPackageDefinition = namedtuple("PipPackageDefinition", ["pkg", "version"])


@contextlib.contextmanager
def current_directory(dir: Path):
    """
    Changes the current working directory to the specified one and reverts
    to the previous one on exit.
    """
    previous = Path.cwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(previous)


class Workspace:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    @classmethod
    def for_slc(cls, name: str) -> Workspace:
        return cls(Path.cwd() / constants.WORKSPACE_DIR / name)

    @property
    def git_clone_path(self) -> Path:
        """
        Returns the path for cloning Git repository
        script-languages-container-release.
        """
        return self.root_dir / "git-clone"

    @property
    def export_path(self) -> Path:
        """
        Returns the export path for script-languages-container
        """
        return self.root_dir / "container"

    @property
    def output_path(self) -> Path:
        """
        Returns the output path containing caches and logs.
        """
        return self.root_dir / "output"

    def cleanup_output_path(self) -> None:
        """
        Remove the output path recursively.
        """
        shutil.rmtree(self.output_path)

    def cleanup_export_path(self) -> None:
        """
        Remove the export path recursively
        """
        shutil.rmtree(self.export_path)


def clone_slc_repo(target_dir: Path):
    """
    Clones the script-languages-release repository from Github into
    the target dir configured in the Secure Configuration Storage.
    """
    dir = target_dir
    if dir.is_dir():
        LOG.warning(f"Directory '{dir}' is not empty. Skipping checkout....")
        return

    dir.mkdir(parents=True, exist_ok=True)
    LOG.info(f"Cloning into {dir}...")
    repo = Repo.clone_from(
        "https://github.com/exasol/script-languages-release",
        dir,
        branch=constants.SLC_RELEASE_TAG,
    )
    LOG.info("Fetching submodules...")
    repo.submodule_update(recursive=True)


class ScriptLanguageContainer:
    """
    Support building different flavors of Exasol Script Language
    Containers (SLCs) using the SLCT.

    Parameter ``name`` serves as a key for the related flavor stored in the
    Secure Configuration Storage (SCS / secrets / conf).  The flavor is used
    as a template for building the SLC.

    If the flavor is missing in the SCS or the SLC Git repository has not been
    checked out (i.e. cloned) into the checkout_dir, then the constructor will
    raise an SlcError.

    Additionally, the caller needs to ensure, that a flavor with this name is
    contained in the SLC release specified in variable
    constants.SLC_RELEASE_TAG.
    """

    def __init__(
        self,
        secrets: Secrets,
        name: str,
    ):
        self.secrets = secrets
        self.name = name
        self.flavor = SlcFlavor(name).verify(secrets)
        self.workspace = Workspace.for_slc(name)
        if not self.flavor_path.is_dir():
            raise SlcError(
                f"SLC Git repository not checked out to {self.checkout_dir}."
            )

    @classmethod
    def create(
        cls,
        secrets: Secrets,
        name: str,
        flavor: str,
    ) -> ScriptLanguageContainer:
        slc_flavor = SlcFlavor(name)
        if slc_flavor.exists(secrets):
            raise SlcError(
                "Secure Configuration Storage already contains a"
                f" flavor for SLC name {name}."
            )
        slc_flavor.save(secrets, flavor)
        workspace = Workspace.for_slc(name)
        clone_slc_repo(workspace.git_clone_path)
        return cls(secrets=secrets, name=name)

    @property
    def language_alias(self) -> str:
        """
        Is case-insensitive.
        """
        return f"custom_slc_{self.name}"

    @property
    def checkout_dir(self) -> Path:
        return self.workspace.git_clone_path

    @property
    def _flavor_path_rel(self) -> str:
        return str(self.flavor_path.relative_to(self.checkout_dir))

    @property
    def flavor_path(self) -> Path:
        return self.checkout_dir / constants.FLAVORS_PATH_IN_SLC_REPO / self.flavor

    @property
    def custom_pip_file(self) -> Path:
        """
        Returns the path to the custom pip file of the flavor
        """
        return (
            self.flavor_path
            / "flavor_customization"
            / "packages"
            / "python3_pip_packages"
        )

    def export(self):
        """
        Exports the current SLC to the export directory.
        """
        with current_directory(self.checkout_dir):
            exaslct_api.export(
                flavor_path=(str(self._flavor_path_rel),),
                export_path=str(self.workspace.export_path),
                output_directory=str(self.workspace.output_path),
                release_name=self.language_alias,
            )

    def deploy(self):
        """
        Deploys the current script-languages-container to the database and
        stores the activation string in the Secure Configuration Storage.
        """
        bfs_params = {
            k: self.secrets.get(v)
            for k, v in [
                ("bucketfs_host", CKey.bfs_host_name),
                ("bucketfs_port", CKey.bfs_port),
                ("bucketfs_user", CKey.bfs_user),
                ("bucketfs_password", CKey.bfs_password),
                ("bucketfs_name", CKey.bfs_service),
                ("bucket", CKey.bfs_bucket),
            ]
        }

        with current_directory(self.checkout_dir):
            exaslct_api.deploy(
                flavor_path=(str(self._flavor_path_rel),),
                **bfs_params,
                path_in_bucket=constants.PATH_IN_BUCKET,
                release_name=self.language_alias,
                output_directory=str(self.workspace.output_path),
            )
            container_name = f"{self.flavor}-release-{self.language_alias}"
            result = exaslct_api.generate_language_activation(
                flavor_path=str(self._flavor_path_rel),
                bucketfs_name=bfs_params["bucketfs_name"],
                bucket_name=bfs_params["bucket"],
                container_name=container_name,
                path_in_bucket=constants.PATH_IN_BUCKET,
            )
            alter_session_cmd = result[0]
            re_res = re.search(
                r"ALTER SESSION SET SCRIPT_LANGUAGES='(.*)'", alter_session_cmd
            )
            activation_key = re_res.groups()[0]
            _, url = activation_key.split("=", maxsplit=1)
            self.secrets.save(self._alias_key, f"{self.language_alias}={url}")

    @property
    def _alias_key(self):
        return constants.SLC_ACTIVATION_KEY_PREFIX + self.language_alias

    @property
    def activation_key(self) -> str:
        """
        Returns the language activation string for the uploaded script-language-container.
        Can be used in `ALTER SESSION` or `ALTER_SYSTEM` SQL commands to activate
        the language of the uploaded script-language-container.
        """
        try:
            return self.secrets[self._alias_key]
        except AttributeError as ex:
            raise SlcError(
                "Secure Configuration Storage does not contains an activation key."
            ) from ex

    def append_custom_packages(self, pip_packages: list[PipPackageDefinition]):
        """
        Appends packages to the custom pip file.

        Note: This method is not idempotent: Multiple calls with the same
        package definitions will result in duplicate entries.
        """
        with open(self.custom_pip_file, "a") as f:
            for p in pip_packages:
                print(f"{p.pkg}|{p.version}", file=f)

    @property
    def docker_images(self) -> list[str]:
        """
        Return list of Docker image tags related to the current SLC.
        """
        image_name = constants.SLC_DOCKER_IMG_NAME
        prefix = f"{image_name}:{self.flavor}"
        with ContextDockerClient() as docker_client:
            images = docker_client.images.list(name=image_name)
            return [tag for img in images if (tag := img.tags[0]).startswith(prefix)]

    def clean_docker_images(self):
        """
        Deletes local docker images related to the current SLC.
        """
        with current_directory(self.checkout_dir):
            exaslct_api.clean_flavor_images(
                flavor_path=(str(self._flavor_path_rel),),
                output_directory=str(self.workspace.output_path),
            )
