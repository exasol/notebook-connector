import exasol.nb_connector.cli.commands  # noqa: F401
from exasol.nb_connector.cli.groups import (
    ai_lab_cli,
    scs_cli,
)


def scs_main():
    scs_cli()


def ai_lab_main():
    ai_lab_cli()


if __name__ == "__main__":
    scs_main()
