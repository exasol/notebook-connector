import click
from exasol.nb_connector.cli.groups import cli
from enum import Enum


class Backend(Enum):
    ONPREM = "onprem"
    SAAS = "saas"
    DOCKER_DB = "docker-db"

    @classmethod
    def help(cls):
        return [x.value for x in cls]


@cli.command()
@click.option(
    "--backend",
    metavar="BACKEND",
    required=True,
    # show_choices=True,
    # show_default=True,
    type=click.Choice(Backend.help(), case_sensitive=False),
    help=f"Exasol backend for which to check the parameters, one of {Backend.help()}",
)
def check(backend: str):
    b = Backend(backend)
    print(f'{b}')
