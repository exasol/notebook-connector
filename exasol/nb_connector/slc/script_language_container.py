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

from exasol.nb_connector.ai_lab_config import AILabConfig
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.language_container_activation import ACTIVATION_KEY_PREFIX
from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc import constants
from exasol.nb_connector.slc.slc_session import (
    SlcError,
    SlcSession,
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


def clone_slc_repo(session: SlcSession):
    """
    Clones the script-languages-release repository from Github into
    the target dir configured in the Secure Configuration Storage.
    """
    dir = session.checkout_dir
    if dir.is_dir():
        LOG.warning(f"Directory '{dir}' is not empty. Skipping cloning....")
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

    Parameter name serves as a key for different SLC sessions. Each session is
    associated with SLC-related properties stored in the Secure Configuration
    Storage (SCS / secrets / conf):

    * flavor
    * language_alias
    * checkout_dir

    If parameter verify is True, and one of these properties is missing in the
    SCS, then the constructor will raise an SlcError.

    Additionally, the caller needs to ensure, that a flavor with this name is
    contained in the SLC release specified in variable
    constants.SLC_RELEASE_TAG.
    """

    def __init__(
        self,
        secrets: Secrets,
        name: str,
    ):
        self.session = SlcSession(secrets, name)
        self.workspace = Workspace(Path.cwd())
        self.session.verify()
        if not self.session.flavor_dir.is_dir():
            raise SlcError(
                f"SLC Git repository not checked out to {self.session.checkout_dir}."
            )

    @classmethod
    def create(
        cls,
        secrets: Secrets,
        name: str,
        flavor: str,
    ) -> ScriptLanguageContainer:
        session = SlcSession(secrets=secrets, name=name)
        checkout_dir = Path.cwd() / constants.SLC_CHECKOUT_DIR / name
        session.save(
            flavor=flavor,
            checkout_dir=checkout_dir,
        )
        clone_slc_repo(session)
        return cls(secrets=secrets, name=name)

    @property
    def name(self) -> str:
        return self.session.name

    @property
    def flavor(self) -> str:
        return self.session.flavor

    @property
    def language_alias(self) -> str:
        return self.session.language_alias

    @property
    def flavor_path(self) -> str:
        return str(self.session.flavor_path_in_slc_repo)

    def export(self):
        """
        Exports the current SLC to the export directory.
        """
        with current_directory(self.session.checkout_dir):
            exaslct_api.export(
                flavor_path=(self.flavor_path,),
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
            k: self.session.secrets.get(v)
            for k, v in [
                ("bucketfs_host", CKey.bfs_host_name),
                ("bucketfs_name", CKey.bfs_service),
                ("bucket_name", CKey.bfs_bucket),
                ("bucketfs_port", CKey.bfs_port),
                ("bucketfs_username", CKey.bfs_user),
                ("bucketfs_password", CKey.bfs_password),
            ]
        }

        with current_directory(self.session.checkout_dir):
            exaslct_api.deploy(
                flavor_path=(self.flavor_path,),
                **bfs_params,
                path_in_bucket=constants.PATH_IN_BUCKET,
                release_name=self.language_alias,
                output_directory=str(self.workspace.output_path),
            )
            container_name = f"{self.flavor}-release-{self.language_alias}"
            result = exaslct_api.generate_language_activation(
                flavor_path=self.flavor_path,
                bucketfs_name=bucketfs_name,
                bucket_name=bucket_name,
                container_name=container_name,
                path_in_bucket=constants.PATH_IN_BUCKET,
            )
            alter_session_cmd = result[0]
            re_res = re.search(
                r"ALTER SESSION SET SCRIPT_LANGUAGES='(.*)'", alter_session_cmd
            )
            activation_key = re_res.groups()[0]
            _, url = activation_key.split("=", maxsplit=1)
            self.session.secrets.save(self._alias_key, f"{self.language_alias}={url}")

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
            return self.session.secrets[self._alias_key]
        except AttributeError as ex:
            raise SlcError(
                "Secure Configuration Storage does not contains an activation key."
            ) from ex

    def append_custom_packages(self, pip_packages: list[PipPackageDefinition]):
        """
        Appends packages to the custom pip file.

        Note: This method is not idempotent: Multiple calls with the same
        package definitions will result in duplicated entries.
        """
        with open(self.session.custom_pip_file, "a") as f:
            for p in pip_packages:
                print(f"{p.pkg}|{p.version}", file=f)

    @property
    def docker_images(self) -> list[str]:
        image_name = "exasol/script-language-container"
        with ContextDockerClient() as docker_client:
            images = docker_client.images.list(name=image_name)
            image_tags = [img.tags[0] for img in images]
            return [
                tag
                for tag in image_tags
                if tag.startswith(f"{image_name}:{self.flavor}")
            ]

    def clean_docker_images(self):
        """
        Deletes local docker images related to the current flavor.
        """
        exaslct_api.clean_flavor_images(
            flavor_path=(self.flavor_path,),
            output_directory=str(self.workspace.output_path),
        )
