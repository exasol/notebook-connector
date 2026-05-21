import sys

import exasol.nb_connector.cli.commands  # noqa: F401
from exasol.nb_connector.cli.groups import (
    ai_lab_cli,
    scs_cli,
)


def scs_main():
    scs_cli()


def ai_lab_main():
    ai_lab_cli()


def _module_main():
    """
    Support direct module execution in tests by selecting the CLI group based
    on the subcommand being invoked.
    """
    ai_lab_commands = {"start", "deploy-notebooks"}
    if len(sys.argv) > 1 and sys.argv[1] in ai_lab_commands:
        ai_lab_cli()
    else:
        scs_cli()


if __name__ == "__main__":
    _module_main()
