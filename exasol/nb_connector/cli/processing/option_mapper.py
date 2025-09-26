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
from exasol.nb_connector.cli.param_wrappers import ScsOption
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
) -> list[ScsOption]:
    def specific_options():
        if backend == StorageBackend.saas:
            return SAAS_OPTIONS
        if backend != StorageBackend.onprem:
            raise ScsCliError(f"Unsupported backend {backend}")
        return DOCKER_DB_OPTIONS if use_itde else ONPREM_OPTIONS

    return [SELECT_BACKEND_OPTION, USE_ITDE_OPTION] + specific_options()


class OptionMapper:
    """
    Map arguments to initial definitions of click
    parameters. E.g. "db_username" to "--db-username".
    """

    def __init__(self, scs: Secrets, backend: StorageBackend, use_itde: bool):
        self.scs = scs
        self.options = get_options(backend, use_itde)

    def find_option(self, arg_name: str) -> ScsOption:
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

    def set_dynamic_defaults(self, values: dict[str, Any]) -> dict[str, Any]:
        """
        Some options may specify another option to get their default value
        from, e.g. --bucketfs-host-internal reads its default value from
        --bucketfs-host.
        """
        for o in self.options:
            ref = o.scs_key and o.get_default_from
            if ref and values[o.arg_name] is None:
                other = self.find_option(ref)
                report.info(
                    f"Using {other.cli_option()} as default for {o.cli_option()}."
                )
                values[o.arg_name] = values[other.arg_name]
        return values

    def check(self) -> bool:
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
            return True
        formatted = ", ".join(missing)
        n = len(missing)
        prefix = "1 option is" if n == 1 else f"{n} options are"
        report.error(f"{prefix} not yet configured: {formatted}.")
        return False


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


def get_option_mapper(scs_file: Path) -> OptionMapper | None:
    """
    Return an instance of an OptionMapper if the SCS contains a proper
    backend selection. Otherwise report an error and return None.
    """

    scs = get_scs(scs_file)
    config = BackendSelector(scs)
    if not config.knows_backend:
        report.error(f"SCS {scs_file} does not contain any backend.")
        return None
    if not config.knows_itde_usage:
        report.error(
            f"SCS {scs_file} does not contain whether "
            "to use an Exasol Docker instance (ITDE)."
        )
        return None
    return OptionMapper(scs, config.backend, config.use_itde)
