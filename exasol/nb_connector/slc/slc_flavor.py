from __future__ import annotations

import re
from pathlib import Path

from exasol.nb_connector.secret_store import Secrets

NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$", flags=re.IGNORECASE)


class SlcError(Exception):
    """
    Signals errors related to ScriptLanguageContainer:

    * The name of the SLC is not unique

    * the Secure Configuration Storage (SCS / secrets / conf) does not contain
      a required option

    * The SLC Git repository has not been checked out (cloned)
    """


class SlcFlavor:
    # def __init__(self, slc_name: str, slc_dir: Path):
    def __init__(self, slc_name: str):
        if not NAME_PATTERN.match(slc_name):
            raise SlcError(
                f'SLC name "{slc_name}" doesn\'t match'
                f' regular expression "{NAME_PATTERN}".'
            )
        self.slc_name = slc_name
        # self.slc_dir = slc_dir

    @property
    def key(self):
        return f"SLC_FLAVOR_{self.slc_name.upper()}"

    def save(self, secrets: Secrets, flavor: str) -> None:
        secrets.save(self.key, flavor)

    def get(self, secrets: Secrets) -> str:
        return secrets[self.key]

    def exists(self, secrets: Secrets) -> bool:
        return secrets.get(self.key)

    def verify(self, secrets: Secrets) -> SlcFlavor:
        try:
            secrets[self.key]
        except AttributeError as ex:
            raise SlcError(
                "Secure Configuration Storage does not contain a"
                f" flavor for SLC {self.slc_name}."
            ) from ex
        return self
