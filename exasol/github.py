"""
Github-related utility functions - check for latest release of project, retrieval of artefacts, etc.
"""
import enum
import requests
import pathlib
import logging
from typing import Tuple, Optional

_logger = logging.getLogger(__name__)


class Project(enum.Enum):
    """
    Names of github projects to be retrieved. Values have to match github project names.
    """
    CLOUD_STORAGE_EXTENSION = "cloud-storage-extension"
    KAFKA_CONNECTOR_EXTENSION = "kafka-connector-extension"


def get_latest_version_and_jar_url(project: Project) -> Tuple[str, str]:
    """
    Retrieves the latest version of stable project release
    and url with jar file from the release.

    :param project: name of the project
    :return: tuple with version and url to retrieve the artefact.
    """
    r = requests.get(f"https://api.github.com/repos/exasol/{project.value}/releases/latest")
    if r.status_code != 200:
        raise RuntimeError("Error sending request to the github api, code: %d" % r.status_code)
    data = r.json()
    version = data.get('tag_name')
    if version is None:
        raise RuntimeError(f"The latest version of {project.value} has no tag, something is wrong")
    for asset in data.get('assets', []):
        name = asset['name']
        if name.endswith(f"{version}.jar"):
            dl_url = asset['browser_download_url']
            return version, dl_url
    raise RuntimeError("Could not find proper jar url for the latest release")


def retrieve_jar(project: Project, use_local_cache: bool = True,
                 storage_path: Optional[pathlib.Path] = None) -> pathlib.Path:
    """
    Returns latest jar file for the project, possibly using local cache.
    :param project: project to be used
    :param use_local_cache: should local cache be used or file always retrieved anew
    :param storage_path: path to be used for downloading. If None, current directory will be used.
    :return: path to the jar file on the local filesystem
    """
    version, jar_url = get_latest_version_and_jar_url(project)
    _, local_jar_name = jar_url.rsplit('/', maxsplit=1)
    local_jar_path = pathlib.Path(local_jar_name)
    if storage_path is not None:
        if not storage_path.exists():
            raise ValueError(f"Local storage path doesn't exist: {storage_path}")
        local_jar_path = storage_path / local_jar_path

    if use_local_cache and local_jar_path.exists():
        _logger.info(f"Jar for version {version} already exists in {local_jar_path}, skip downloading")
    else:
        _logger.info(f"Fetching jar for version {version} from {jar_url}...")
        r = requests.get(jar_url, stream=True)
        try:
            count_bytes = local_jar_path.write_bytes(r.content)
            _logger.info(f"Saved {count_bytes} bytes in {local_jar_path}")
        finally:
            r.close()
    return local_jar_path
