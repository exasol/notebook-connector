from __future__ import annotations

import logging
import traceback
from enum import Enum
from pathlib import Path
from typing import Any

import click

from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.cli import reporting as report
from exasol.nb_connector.cli.param_wrappers import ScsSecretOption
from exasol.nb_connector.cli.processing.backend_selector import BackendSelector
from exasol.nb_connector.cli.processing.bucketfs_access import verify_bucketfs_access
from exasol.nb_connector.cli.processing.option_set import (
    SELECT_BACKEND_OPTION,
    USE_ITDE_OPTION,
    OptionSet,
    ScsCliError,
    get_option_set,
    get_scs,
)
from exasol.nb_connector.connections import open_pyexasol_connection
from exasol.nb_connector.secret_store import Secrets

LOG = logging.getLogger(__name__)


def save(
    scs_file: Path,
    backend: StorageBackend,
    use_itde: bool,
    values: dict[str, Any],
):
    """
    Save the provided values to SCS using the keys inferred from backend
    and use_itde.
    """
    scs = get_scs(scs_file)
    config = BackendSelector(scs)
    if not config.matches(backend, use_itde):
        report.warning(
            "Overwriting former SCS configuration for an "
            f"Exasol {config.backend_name} instance."
        )
    options = OptionSet(scs, backend, use_itde)
    values[SELECT_BACKEND_OPTION.arg_name] = backend.name
    values[USE_ITDE_OPTION.arg_name] = use_itde
    values.update(options.default_values(values))
    for arg_name, value in values.items():
        if value is None:
            continue
        option = options.find_option(arg_name)
        if not option.scs_key:
            continue
        if not isinstance(option, ScsSecretOption):
            content = value.value if isinstance(value, Enum) else str(value)
            scs.save(option.scs_key, content)
            continue
        if secret := option.get_secret(interactive=bool(value)):
            scs.save(option.scs_key, secret)


def verify_connection(scs: Secrets) -> None:
    """
    Verify if successful connection to the configured backend is possible.
    Raise an ScsCliError otherwise.
    """
    try:
        open_pyexasol_connection(scs).execute("SELECT 1 FROM DUAL").fetchone()
    except Exception as ex:
        stacktrace = traceback.format_exc()
        raise ScsCliError(
            f"Failed to connect to the configured database {stacktrace}"
        ) from ex
    report.success("Connection to the configured database instance was successful.")


def check_scs(scs_file: Path, connect: bool) -> None:
    """
    Check the SCS content for completeness.  Infer the required keys from
    backend and use_itde if these are contained in the SCS already.

    If parameter `connect` is True then also verify if a connection to the
    configured Exasol database instance is successful.

    The function raises an ScsCliError in any of the following cases:

    * The SCS does not select any backend.

    * The options are incomplete for configuring access to the selected backend.

    * Connecting to the configured backend was requested but failed.

    For Docker-DB (ITDE) the connection is not verified currently, as

    * Startup of ITDE takes quite some time which is considered inconvienient
      for the user

    * Connect does not verify parameters actually configured by the user but
      rather parameters selected by ITDE
    """
    options = get_option_set(scs_file)
    options.check()
    if not connect:
        return
    scs = options.scs
    if BackendSelector(scs).use_itde:
        report.warning(
            "Connection verification for Docker-DB"
            " (via ITDE) is not implemented, yet."
        )
        return
    verify_connection(scs)
    verify_bucketfs_access(scs)


def show_scs_content(scs_file: Path) -> None:
    """
    If the SCS contains a proper backend selection, then show the SCS
    content for this context.
    """
    option_set = get_option_set(scs_file)
    for option in option_set.options:
        value = option.scs_key and option.displayed_value(option_set.scs)
        if value is not None:
            value = value or '""'
            click.echo(f"{option.cli_option()}: {value}")
