from __future__ import annotations

import getpass
import os
from pathlib import Path
from typing import Any

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.cli import reporting as report
from exasol.nb_connector.cli.options import (
    DOCKER_DB_OPTIONS,
    ONPREM_OPTIONS,
    SAAS_OPTIONS,
)
from exasol.nb_connector.cli.param_wrappers import (
    ScsOption,
    ScsParam,
)
from exasol.nb_connector.cli.processing.backend_selector import BackendSelector
from exasol.nb_connector.secret_store import Secrets


class ScsCliError(Exception):
    """
    Indicates an error when saving or checking CLI options wrt. the Secure
    Configuration Storage (SCS).
    """


SELECT_BACKEND_OPTION = ScsOption("backend", scs_key=CKey.storage_backend)
USE_ITDE_OPTION = ScsOption("use_itde", scs_key=CKey.use_itde)


def get_options(
    backend: StorageBackend,
    use_itde: bool,
) -> list[ScsParam]:
    def specific_options():
        if backend == StorageBackend.saas:
            return SAAS_OPTIONS
        if backend != StorageBackend.onprem:
            raise ScsCliError(f"Unsupported backend {backend}")
        return DOCKER_DB_OPTIONS if use_itde else ONPREM_OPTIONS

    return [SELECT_BACKEND_OPTION, USE_ITDE_OPTION] + specific_options()


class OptionSet:
    """
    * Find an option by its underscored name.

    * Transfer option values as default to other options.

    * Check the SCS content for completeness.
    """

    def __init__(self, scs: Secrets, backend: StorageBackend, use_itde: bool):
        self.scs = scs
        self.options = get_options(backend, use_itde)

    def default_values(self, values: dict[str, Any]) -> dict[str, Any]:
        """
        Return a dict of option arg names and default values.

        The dict contains only entries for options with a defined default
        value, that are neither specified explicitly, nor stored in the SCS,
        yet.

        For details, see https://github.com/exasol/notebook-connector/issues/285.
        """

        def use_default(option: ScsParam) -> bool:
            return bool(
                option.default is not None
                and values.get(option.arg_name) is None
                and option.scs_key
                and self.scs.get(option.scs_key) is None
            )

        return {o.arg_name: o.default for o in self.options if use_default(o)}

    def find_option(self, arg_name: str) -> ScsParam:
        """
        Find the full definition of a click parameter for the specified
        arg name.
        """
        try:
            return next(o for o in self.options if o.arg_name == arg_name)
        except StopIteration:
            raise ScsCliError(
                f"Couldn't find any option with parameter name {arg_name}."
            )

    def check(self):
        """
        Check if the content of the SCS is complete wrt. the selected
        backend as the required options depend on the selected backend.
        """
        missing = [
            o.cli_option(full=True) for o in self.options if o.needs_entry(self.scs)
        ]
        if not missing:
            config = BackendSelector(self.scs)
            report.success(
                "Configuration is complete for an "
                f"Exasol {config.backend_name} instance."
            )
            return
        formatted = ", ".join(missing)
        n = len(missing)
        prefix = "1 option is" if n == 1 else f"{n} options are"
        raise ScsCliError(f"{prefix} not yet configured: {formatted}.")


def get_scs_master_password():
    """
    Retrieve the master password for the SCS either from the related
    environment variable or by asking the user to type the password
    interactively.
    """
    if from_env := os.getenv("SCS_MASTER_PASSWORD"):
        return from_env
    return getpass.getpass("SCS master password: ")


def get_scs(scs_file: Path) -> Secrets:
    scs_password = get_scs_master_password()
    return Secrets(scs_file, scs_password)


def get_option_set(scs_file: Path) -> OptionSet:
    """
    Return an instance of an OptionSet if the SCS contains a proper
    backend selection. Otherwise raise an ScsCliError.

    This function is designed to be called only once in the CLI application.
    Otherwise it will always ask for the SCS master password and potentially
    report errors in case of no backend being selected.

    If you want to instantiate the OptionSet more often, then simply use
    its constructor.
    """

    scs = get_scs(scs_file)
    config = BackendSelector(scs)
    if not config.knows_backend:
        raise ScsCliError(f"SCS {scs_file} does not contain any backend.")
    return OptionSet(scs, config.backend, config.use_itde)
