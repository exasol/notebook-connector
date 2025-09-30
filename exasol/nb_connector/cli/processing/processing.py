from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any

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
    get_scs,
)

LOG = logging.getLogger(__name__)


def save(
    scs_file: Path,
    backend: StorageBackend,
    use_itde: bool,
    values: dict[str, Any],
) -> int:
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
    return 0
