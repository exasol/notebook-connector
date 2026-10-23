"""
Github-related utility functions - check for latest release of
project, retrieval of artefacts, etc.
"""

import enum
import logging
import pathlib

import requests

_logger = logging.getLogger(__name__)

import logging
from pathlib import Path
from typing import Any


class Project(enum.Enum):
    """
    Names of github projects to be retrieved. Values have to
    match github project names.
    """

    CLOUD_STORAGE_EXTENSION = "cloud-storage-extension"
    KAFKA_CONNECTOR_EXTENSION = "kafka-connector-extension"


def _release_name(release: dict[str, Any]) -> str:
    value = release.get("name") or release.get("html_url", "(empty URL)")
    return str(value)


class GithubReleaseError(RuntimeError):
    """
    Signals an error when retrieving the URL of an artifact on GitHub.
    """


def get_latest_version_and_jar_url(project: Project) -> tuple[str, str]:
    """
    Retrieves the latest version of stable project release
    and url with jar file from the release.

    :param project: name of the project
    :return: tuple with version and url to retrieve the artefact.
    """
    url = f"https://api.github.com/repos/exasol/{project.value}/releases/latest"
    req = requests.get(url, timeout=10)
    if req.status_code != 200:
        raise GithubReleaseError(
            f"{url} returned status code {req.status_code}: {req.text[:200]}."
        )
    release = req.json()
    if not (tag := release.get("tag_name")):
        raise GithubReleaseError(
            f'The latest release "{_release_name(release)}" of {project.value} has no tag.'
        )
    suffix = f"{tag}.jar"
    for asset in release.get("assets", []):
        name = asset["name"]
        if name.endswith(suffix):
            dl_url = asset["browser_download_url"]
            return tag, dl_url
    raise GithubReleaseError(
        f'Could not find asset with suffix "{suffix}" attached '
        f'to the latest release "{_release_name(release)}".'
    )


def retrieve_jar(
    project: Project,
    use_local_cache: bool = True,
    storage_path: pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Returns latest jar file for the project, possibly using local cache.

    :param project: project to be used
    :param use_local_cache: should local cache be used or file always retrieved anew
    :param storage_path: path to be used for downloading.
        If None, current directory will be used.
    :return: path to the jar file on the local filesystem
    """
    version, jar_url = get_latest_version_and_jar_url(project)
    _, local_jar_name = jar_url.rsplit("/", maxsplit=1)
    local_jar_path = pathlib.Path(local_jar_name)
    if storage_path is not None:
        if not storage_path.exists():
            raise ValueError(f"Local storage path doesn't exist: {storage_path}")
        local_jar_path = storage_path / local_jar_path

    if use_local_cache and local_jar_path.exists():
        _logger.info(
            "Jar for version %s already exists in %s, skip downloading",
            version,
            local_jar_path,
        )
    else:
        _logger.info("Fetching jar for version %s from %s...", version, jar_url)
        req = requests.get(jar_url, stream=True, timeout=10)
        try:
            count_bytes = local_jar_path.write_bytes(req.content)
            _logger.info("Saved %d bytes in %s", count_bytes, local_jar_path)
        finally:
            req.close()
    return local_jar_path
