import click

from exasol.nb_connector.ai_lab_config import Accelerator
from exasol.nb_connector.ai_lab_config import AILabConfig as CKey
from exasol.nb_connector.cli.scs_options import ScsOption

EXTRA_DOCKER_DB_OPTIONS = [
    ScsOption(
        "--db-mem-size",
        type=int,
        metavar="GiB",
        default=2,
        show_default=True,
        help="Database memory size (GiB)",
        scs_key=CKey.mem_size,
    ),
    ScsOption(
        "--db-disk-size",
        metavar="GiB",
        type=int,
        default=2,
        show_default=True,
        help="Database disk size (GiB)",
        scs_key=CKey.disk_size,
    ),
    ScsOption(
        "--accelerator",
        type=click.Choice(Accelerator, case_sensitive=False),
        default="none",
        show_default=True,
        help="Hardware acceleration",
        scs_key=CKey.accelerator,
    ),
]
