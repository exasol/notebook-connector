import exasol.nb_connector.cli.commands  # noqa: F401  – registers all commands with cli
from exasol.nb_connector.cli.groups import cli


def main():
    cli()


if __name__ == "__main__":
    main()
