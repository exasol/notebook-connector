import logging
from dataclasses import dataclass
from pathlib import Path

from exasol.nb_connector.secret_store import Secrets
from exasol.nb_connector.slc.constants import FLAVORS_PATH_IN_SLC_REPO

LOG = logging.getLogger(__name__)


class SlcSessionError(Exception):
    """
    In case the Secure Configuration Storage (SCS / secrets / conf) does
    not contain specific data required for using the ScriptLanguageContainer.

    E.g. the flavor for the specified SLC session or the SLC target directory.
    """


@dataclass
class ConfigurationItem:
    secrets: Secrets
    key_prefix: str
    session_name: str
    description: str

    @property
    def key(self) -> str:
        return f"{self.key_prefix}_{self.session_name}"

    def save(self, value: str) -> None:
        if self.secrets.get(self.key) is not None:
            raise SlcSessionError(
                "Secure Configuration Storage already contains an"
                f" {self.description} for session {self.session_name}."
            )
        self.secrets.save(self.key, value)

    @property
    def value(self) -> str:
        try:
            return self.secrets[self.key]
        except AttributeError as ex:
            raise SlcSessionError(
                "Secure Configuration Storage does not contain an"
                f" {self.description} for session {self.session_name}."
            ) from ex


class SlcSession:
    # DEFAULT_NAME = "DEFAULT"
    # DEFAULT_FLAVOR = "template-Exasol-all-python-3.10"

    def __init__(self, secrets: Secrets, name: str):
        self.secrets = secrets
        self.name = name
        self._checkout_dir = ConfigurationItem(
            secrets, "SLC_DIR", name, "SLC target directory")
        self._flavor = ConfigurationItem(
            secrets, "SLC_FLAVOR", name, "SLC flavor")
        self._language_alias = ConfigurationItem(
            secrets, "SLC_LANGUAGE_ALIAS", name, "SLC language alias")

    @property
    def flavor_name(self) -> str:
        return self._flavor.value

    @property
    def checkout_dir(self) -> Path:
        return Path(self._checkout_dir.value)

    @property
    def language_alias(self) -> Path:
        return self._language_alias.value

    @property
    def flavor_path_in_slc_repo(self) -> Path:
        """
        Path to the used flavor within the script-languages-release
        repository
        """
        return FLAVORS_PATH_IN_SLC_REPO / self.flavor_name

    @property
    def flavor_dir(self) -> Path:
        return self.checkout_dir / self.flavor_path_in_slc_repo

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

    def save(
        self,
        flavor_name: str,
        language_alias: str,
        checkout_dir: Path,
    ) -> None:
        """
        Save the specified flavor_name into the SCS using the slc_session
        name as key.
        """
        self._flavor.save(flavor_name)
        self._language_alias.save(language_alias)
        self._checkout_dir.save(str(checkout_dir))
