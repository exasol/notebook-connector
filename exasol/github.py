"""
Github-related utility functions - check for latest release of project, retrieval of artefacts, etc.
"""
import requests
from typing import Tuple


def get_latest_version_and_jar_url(project: str) -> Tuple[str, str]:
    """
    Retrieves the latest version of stable project release
    and url with jar file from the release.

    :param project: name of the project
    :return: tuple with version and url to retrieve the artefact.
    """
    r = requests.get(f"https://api.github.com/repos/exasol/{project}/releases/latest")
    if r.status_code != 200:
        raise RuntimeError("Error sending request to the github api, code: %d" % r.status_code)
    data = r.json()
    version = data.get('tag_name')
    if version is None:
        raise RuntimeError(f"The latest version of {project} has no tag, something is wrong")
    for asset in data.get('assets', []):
        name = asset['name']
        if name.endswith(f"{version}.jar"):
            dl_url = asset['browser_download_url']
            return version, dl_url
    raise RuntimeError("Could not find proper jar url for the latest release")
