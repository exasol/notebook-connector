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

    I.e. the flavor, language_alias, or checkout_dir for the specified SLC
    session.
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
    # DEFAULT_FLAVOR = "template-Exasol-all-python-3.10"

    def __init__(self, secrets: Secrets, name: str, verify: bool = True):
        self.secrets = secrets
        self.name = name
        self._atts = {
            key: ConfigurationItem(secrets, prefix, name, description)
            for key, prefix, description in [
                ("flavor", "SLC_FLAVOR", "SLC flavor"),
                ("language_alias", "SLC_LANGUAGE_ALIAS", "SLC language alias"),
                ("checkout_dir", "SLC_DIR", "SLC working directory"),
            ]
        }
        if verify:
            for a in self._atts.values():
                a.value

    def __getattr__(self, property: str) -> str:
        return self._atts[property].value

    @property
    def checkout_dir(self) -> Path:
        return Path(self._atts["checkout_dir"].value)

    @property
    def flavor_path_in_slc_repo(self) -> Path:
        """
        Path to the used flavor within the script-languages-release
        repository
        """
        return FLAVORS_PATH_IN_SLC_REPO / self.flavor

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
        flavor: str,
        language_alias: str,
        checkout_dir: Path,
    ) -> None:
        """
        Save the specified flavor, language_alias, and checkout_dir into
        the Secure Configuration Storage.
        """
        for k, v in {
            "flavor": flavor,
            "language_alias": language_alias,
            "checkout_dir": str(checkout_dir),
        }.items():
            self._atts[k].save(v)
