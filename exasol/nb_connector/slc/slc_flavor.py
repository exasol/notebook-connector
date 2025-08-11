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
    def __init__(self, slc_name: str):
        if not NAME_PATTERN.match(slc_name):
            raise SlcError(
                f'SLC name "{slc_name}" doesn\'t match'
                f' regular expression "{NAME_PATTERN}".'
            )
        self.slc_name = slc_name

    @property
    def key(self):
        return f"SLC_FLAVOR_{self.slc_name.upper()}"

    def save(self, secrets: Secrets, flavor: str) -> None:
        secrets.save(self.key, flavor)

    def exists(self, secrets: Secrets) -> bool:
        return True if secrets.get(self.key) else False

    def verify(self, secrets: Secrets) -> str:
        try:
            return secrets[self.key]
        except AttributeError as ex:
            raise SlcError(
                "Secure Configuration Storage does not contain a"
                f" flavor for SLC {self.slc_name}."
            ) from ex
