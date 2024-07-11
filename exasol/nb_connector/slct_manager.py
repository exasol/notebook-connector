import os
import re
import contextlib
from pathlib import Path
from exasol_script_languages_container_tool.lib import api as exaslct_api
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey, StorageBackend
from exasol.nb_connector.language_container_activation import ACTIVATION_KEY_PREFIX

EXPORT_PATH = Path() / "container"
OUTPUT_PATH = Path() / "output"
RELEASE_NAME = "current"
PATH_IN_BUCKET = "container"

SLC_SOURCE_FLAVOR_STORE_KEY = "slc_flavor"
SLC_TARGET_DIR_STORE_KEY = "slc_target_dir"


# Activation SQL for the Custom SLC will be saved in the secret
# store with this key.
ACTIVATION_KEY = ACTIVATION_KEY_PREFIX + "slc"

@contextlib.contextmanager
def working_directory(path: Path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)

def check_slc_config(secrets) -> bool:
    slc_dir = Path(secrets.get(SLC_TARGET_DIR_STORE_KEY))
    selected_flavor = secrets.get(SLC_SOURCE_FLAVOR_STORE_KEY)
    print(f"Script-languages repository path is '{slc_dir}'")
    print(f"Selected flavor is '{selected_flavor}'")
    if not (Path(slc_dir) / "flavors" / selected_flavor).is_dir():
        return False

    return True


def get_flavor_path(secrets):
    selected_flavor = secrets.get(SLC_SOURCE_FLAVOR_STORE_KEY)
    return Path("flavors") / selected_flavor

def export(secrets):
    slc_dir = Path(secrets.get(SLC_TARGET_DIR_STORE_KEY))
    flavor_path = get_flavor_path(secrets)
    with working_directory(slc_dir):
        export_result = exaslct_api.export(flavor_path=(str(flavor_path),),export_path=EXPORT_PATH,
                                           output_directory=OUTPUT_PATH)

def upload(secrets):
    slc_dir = Path(secrets.get(SLC_TARGET_DIR_STORE_KEY))
    selected_flavor = secrets.get(SLC_SOURCE_FLAVOR_STORE_KEY)
    flavor_path = get_flavor_path(secrets)

    bucketfs_name = secrets.get(CKey.bfs_service)
    bucket_name = secrets.get(CKey.bfs_bucket)
    database_host = secrets.get(CKey.bfs_host_name)
    bucketfs_port = secrets.get(CKey.bfs_port)
    bucketfs_username = secrets.get(CKey.bfs_user)
    bucketfs_password = secrets.get(CKey.bfs_password)

    with working_directory(slc_dir):
        upload_result = exaslct_api.upload(flavor_path=(str(flavor_path),), database_host=database_host,
                                       bucketfs_name=bucketfs_name,
                                       bucket_name=bucket_name, bucketfs_port=bucketfs_port,
                                       bucketfs_username=bucketfs_username,
                                       bucketfs_password=bucketfs_password, path_in_bucket=PATH_IN_BUCKET,
                                       release_name=RELEASE_NAME)
        container_name = f"{selected_flavor}-release-{RELEASE_NAME}"
        result = exaslct_api.generate_language_activation(flavor_path=flavor_path, bucketfs_name=bucketfs_name,
                                                          bucket_name=bucket_name, container_name=container_name,
                                                          path_in_bucket=PATH_IN_BUCKET)

        alter_session_cmd = result[0]
        re_res = re.search(r"ALTER SESSION SET SCRIPT_LANGUAGES='(.*)'", alter_session_cmd)
        secrets.save(ACTIVATION_KEY, re_res.groups()[0])


