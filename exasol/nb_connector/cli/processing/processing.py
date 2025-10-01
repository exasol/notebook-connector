from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any

import click

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.ai_lab_config import StorageBackend
from exasol.nb_connector.cli import reporting as report
from exasol.nb_connector.cli.param_wrappers import (
    ScsSecretOption,
)
from exasol.nb_connector.cli.processing.backend_selector import (
    BackendSelector,
)
from exasol.nb_connector.cli.processing.option_set import (
    SELECT_BACKEND_OPTION,
    USE_ITDE_OPTION,
    OptionSet,
    ScsCliError,
    get_option_set,
    get_scs,
)
from exasol.nb_connector.connections import open_pyexasol_connection
from exasol.nb_connector.itde_manager import bring_itde_up
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
    options.set_dynamic_defaults(values)
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
    if BackendSelector(scs).use_itde:
        # Question: Is it OK, to let bring_itde_up modify the SCS content, here?
        False and bring_itde_up(scs)
        report.warning(f"Bring up ITDE currently disabled")
        return
    try:
        open_pyexasol_connection(scs).execute("SELECT 1 FROM DUAL").fetchone()
    except Exception as ex:
        raise ScsCliError(f"Failed to connect to the configured database {ex}")
    report.success("Connection to the configured database instance was successful.")


def check_scs(scs_file: Path, connect: bool) -> None:
    """
    Check the SCS content for completeness.  Infer the required keys from
    backend and use_itde if these are contained in the SCS already.

    If parameter `connect` is True then also verify if a connection to the
    configured Exasol database instance is successful.
    """
    options = get_option_set(scs_file)
    options.check()
    if connect:
        verify_connection(options.scs)


def show_scs_content(scs_file: Path) -> None:
    """
    If the SCS contains a proper backend selection, then show the SCS
    content for this context.
    """
    oset = get_option_set(scs_file)
    for o in oset.options:
        value = o.scs_key and o.displayed_value(oset.scs)
        if value is not None:
            value = value or '""'
            click.echo(f"{o.cli_option()}: {value}")
