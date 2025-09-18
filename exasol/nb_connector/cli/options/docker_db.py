import click
from exasol.nb_connector.ai_lab_config import Accelerator


DOCKER_DB_OPTIONS = [
    click.option(
        "--db-mem-size",
        type=int,
        metavar="GiB",
        default=2,
        show_default=True,
        help="Database memory size (GiB)",
    ),
    click.option(
        "--db-disk-size",
        metavar="GiB",
        type=int,
        default=2,
        show_default=True,
        help="Database disk size (GiB)",
    ),
    click.option(
        "--accelerator",
        type=click.Choice(Accelerator, case_sensitive=False),
        default="none",
        show_default=True,
        help="Hardware acceleration",
    ),
]

