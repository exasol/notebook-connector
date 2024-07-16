import logging
import os
import re
import contextlib
from collections import namedtuple
from typing import Optional, List

from git import Repo
from pathlib import Path
from exasol_script_languages_container_tool.lib import api as exaslct_api # type: ignore
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey, AILabConfig
from exasol.nb_connector.language_container_activation import ACTIVATION_KEY_PREFIX
from exasol.nb_connector.secret_store import Secrets

RELEASE_NAME = "current"
PATH_IN_BUCKET = "container"

# Activation SQL for the Custom SLC will be saved in the secret
# store with this key.
ACTIVATION_KEY = ACTIVATION_KEY_PREFIX + "slc"

# This is the flavor customers are supposed to use for modifications.
REQUIRED_FLAVOR = "template-Exasol-all-python-3.10"

# Path to the used flavor within the script-languages-release repository
FLAVOR_PATH_IN_SLC_REPO = Path("flavors") / REQUIRED_FLAVOR

PipPackageDefinition = namedtuple('PipPackageDefinition', ['pkg', 'version'])


class SlcDir:
    def __init__(self, secrets: Secrets):
        self._secrets = secrets

    @property
    def root_dir(self) -> Path:
        target_dir = self._secrets.get(AILabConfig.slc_target_dir)
        if not target_dir:
            raise RuntimeError("slc target dir is not defined in secrets.")
        return Path(target_dir)

    @property
    def flavor_dir(self) -> Path:
        return self.root_dir / FLAVOR_PATH_IN_SLC_REPO

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


class WorkingDir:
    def __init__(self, p: Optional[Path]):
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


class SlctManager:
    def __init__(self, secrets: Secrets, working_path: Optional[Path] = None):
        self.working_path = WorkingDir(working_path)
        self.slc_dir = SlcDir(secrets)
        self._secrets = secrets

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
        Clones the script-languages-release repository from Github into the target dir configured in the secret store.
        """
        if not self.slc_dir.root_dir.is_dir():
            logging.info(f"Cloning into {self.slc_dir}...")
            repo = Repo.clone_from("https://github.com/exasol/script-languages-release", self.slc_dir.root_dir)
            logging.info("Fetching submodules...")
            repo.submodule_update(recursive=True)
        else:
            logging.warning(f"Directory '{self.slc_dir}' already exists. Skipping cloning....")

    def export(self):
        """
        Exports the current script-languages-container to the export directory.
        """
        with self.slc_dir.enter():
            exaslct_api.export(flavor_path=(str(FLAVOR_PATH_IN_SLC_REPO),),
                               export_path=str(self.working_path.export_path),
                               output_directory=str(self.working_path.output_path))

    def upload(self, alias: str):
        """
        Uploads the current script-languages-container to the database
        and stores the activation string in the secret store.
        @param alias: The alias used for the script-language-container activation
        """
        bucketfs_name = self._secrets.get(CKey.bfs_service)
        bucket_name = self._secrets.get(CKey.bfs_bucket)
        database_host = self._secrets.get(CKey.bfs_host_name)
        bucketfs_port = self._secrets.get(CKey.bfs_port)
        bucketfs_username = self._secrets.get(CKey.bfs_user)
        bucketfs_password = self._secrets.get(CKey.bfs_password)

        with self.slc_dir.enter():
            exaslct_api.upload(flavor_path=(str(FLAVOR_PATH_IN_SLC_REPO),),
                               database_host=database_host,
                               bucketfs_name=bucketfs_name,
                               bucket_name=bucket_name, bucketfs_port=bucketfs_port,
                               bucketfs_username=bucketfs_username,
                               bucketfs_password=bucketfs_password, path_in_bucket=PATH_IN_BUCKET,
                               release_name=RELEASE_NAME,
                               output_directory=str(self.working_path.output_path))
            container_name = f"{REQUIRED_FLAVOR}-release-{RELEASE_NAME}"
            result = exaslct_api.generate_language_activation(flavor_path=str(FLAVOR_PATH_IN_SLC_REPO),
                                                              bucketfs_name=bucketfs_name,
                                                              bucket_name=bucket_name, container_name=container_name,
                                                              path_in_bucket=PATH_IN_BUCKET)

            alter_session_cmd = result[0]
            re_res = re.search(r"ALTER SESSION SET SCRIPT_LANGUAGES='(.*)'", alter_session_cmd)
            activation_key = re_res.groups()[0]
            _, url = activation_key.split("=", maxsplit=1)
            self._secrets.save(ACTIVATION_KEY, f"{alias}={url}")

    @property
    def activation_key(self) -> str:
        """
        Returns the language activation string for the uploaded script-language-container.
        Can be used in `ALTER SESSION` or `ALTER_SYSTEM` SQL commands to activate
        the language of the uploaded script-language-container.
        Must not be called after an initial upload.
        """
        activation_key = self._secrets.get(ACTIVATION_KEY)
        if not activation_key:
            raise RuntimeError("SLC activation key not defined in secrets.")
        return activation_key

    @property
    def language_alias(self) -> str:
        """
        Returns the language alias of the uploaded script-language-container.
        Must not be called after an initial upload.
        """
        activation_key = self.activation_key
        alias, _ = activation_key.split("=", maxsplit=1)
        return alias

    @property
    def custom_pip_file(self) -> Path:
        """
        Returns the path to the custom pip file of the flavor
        """
        return self.slc_dir.flavor_dir / "flavor_customization" / "packages" / "python3_pip_packages"

    def append_custom_packages(self, pip_packages: List[PipPackageDefinition]):
        """
        Appends packages to the custom pip file.
        Note: This method is not idempotent: Multiple calls with the same package definitions will result in duplicated entries.
        """
        with open(self.custom_pip_file, "a") as f:
            for p in pip_packages:
                print(f"{p.pkg}|{p.version}", file=f)
