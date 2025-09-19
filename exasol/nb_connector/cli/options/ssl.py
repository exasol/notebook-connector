from pathlib import Path

import click

from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.cli.scs_options import ScsOption

SSL_OPTIONS = [
    ScsOption(
        "--ssl-use-cert-validation/--no-ssl-use-cert-validation",
        type=bool,
        default=True,
        show_default=True,
        help="Whether to validate SSL certificates or not",
        scs_key=CKey.cert_vld,
    ),
    ScsOption(
        "--ssl-cert-path",
        metavar="FILE/DIR",
        type=Path,
        help="SSL trusted CA file/dir",
        scs_key=CKey.trusted_ca,
        scs_required=False,
    ),
]
