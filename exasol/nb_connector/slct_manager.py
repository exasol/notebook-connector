import os
import re
import contextlib
from collections import namedtuple
from typing import Optional, List

from git import Repo
from pathlib import Path
from exasol_script_languages_container_tool.lib import api as exaslct_api
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey, AILabConfig
from exasol.nb_connector.language_container_activation import ACTIVATION_KEY_PREFIX

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


class SlctManager:
    def __init__(self, secrets, working_path: Optional[Path] = None):
        if not working_path:
            self.working_path = Path.cwd()
        else:
            self.working_path = working_path
        self._secrets = secrets

    @property
    def export_path(self):
        """
        Returns the export path for script-languages-container
        """
        return self.working_path / "container"

    @property
    def output_path(self):
        """
        Returns the output path containing caches and logs.
        """
        return self.working_path / "output"

    @contextlib.contextmanager
    def _slc_working_directory(self):
        """Changes working directory and returns to previous on exit."""
        slc_dir = Path(self._secrets.get(AILabConfig.slc_target_dir))
        prev_cwd = Path.cwd()
        os.chdir(slc_dir)
        try:
            yield
        finally:
            os.chdir(prev_cwd)

    def check_slc_repo_complete(self) -> bool:
        """
        Checks if the target dir for the script-languages repository is present and correct.
        """
        slc_dir = Path(self._secrets.get(AILabConfig.slc_target_dir))
        print(f"Script-languages repository path is '{slc_dir}'")
        if not (Path(slc_dir) / FLAVOR_PATH_IN_SLC_REPO).is_dir():
            return False
        return True

    def clone_slc_repo(self):
        """
        Clones the script-languages-release repository from Github into the target dir configured in the secret store.
        """
        slc_dir = Path(self._secrets.get(AILabConfig.slc_target_dir))
        if not slc_dir.is_dir():
            print(f"Cloning into {slc_dir}...")
            repo = Repo.clone_from("https://github.com/exasol/script-languages-release", slc_dir)
            print("Fetching submodules...")
            repo.submodule_update(recursive=True)
        else:
            print(f"Directory '{slc_dir}' already exists. Skipping cloning....")

    def export(self):
        """
        Exports the current script-languages-container to the export directory.
        """
        with self._slc_working_directory():
            exaslct_api.export(flavor_path=(str(FLAVOR_PATH_IN_SLC_REPO),),
                               export_path=str(self.export_path),
                               output_directory=str(self.output_path))

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

        with self._slc_working_directory():
            exaslct_api.upload(flavor_path=(str(FLAVOR_PATH_IN_SLC_REPO),),
                               database_host=database_host,
                               bucketfs_name=bucketfs_name,
                               bucket_name=bucket_name, bucketfs_port=bucketfs_port,
                               bucketfs_username=bucketfs_username,
                               bucketfs_password=bucketfs_password, path_in_bucket=PATH_IN_BUCKET,
                               release_name=RELEASE_NAME,
                               output_directory=str(self.output_path))
            container_name = f"{REQUIRED_FLAVOR}-release-{RELEASE_NAME}"
            result = exaslct_api.generate_language_activation(flavor_path=str(FLAVOR_PATH_IN_SLC_REPO),
                                                              bucketfs_name=bucketfs_name,
                                                              bucket_name=bucket_name, container_name=container_name,
                                                              path_in_bucket=PATH_IN_BUCKET)

            alter_session_cmd = result[0]
            re_res = re.search(r"ALTER SESSION SET SCRIPT_LANGUAGES='(.*)'", alter_session_cmd)
            self._secrets.save(ACTIVATION_KEY, re_res.groups()[0])

    @property
    def activation_key(self) -> str:
        """
        Returns the language activation string for the uploaded script-language-container.
        Can be used in `ALTER SESSION` or `ALTER_SYSTEM` SQL commands to activate
        the language of the uploaded script-language-container.
        Must not be called after an initial upload.
        """
        return self._secrets.get(ACTIVATION_KEY)

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
        return Path(self._secrets.get(
            AILabConfig.slc_target_dir)) / FLAVOR_PATH_IN_SLC_REPO / "flavor_customization" / "packages" / "python3_pip_packages"

    def append_custom_packages(self, pip_packages: List[PipPackageDefinition]):
        """
        Appends packages to the custom pip file.
        Note: This method is not idempotent: Multiple calls with the same package definitions will result in duplicated entries.
        """
        with open(self.custom_pip_file, "a") as f:
            for p in pip_packages:
                print(f"{p.pkg}|{p.version}", file=f)
