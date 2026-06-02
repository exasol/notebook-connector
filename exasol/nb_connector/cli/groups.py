import click


@click.group(name="scs")
def scs_cli():
    """
    Manage application configuration data in the Secure Configuration
    Storage (SCS).

    You can set environment variables SCS_FILE and SCS_MASTER_PASSWORD
    specifying the file containing the SCS and the master password for
    accessing and encrypting the file, respectively.

    Otherwise the scs commands will require the SCS file to be passed as
    positional argument and the master password to be typed interactively.
    """
    pass


@click.group(name="ai-lab")
def ai_lab_cli():
    """
    Start JupyterLab with the bundled notebooks or deploy those notebooks
    into a target directory.
    """
    pass


# The circular import occurs when importing `exasol.nb_connector.cli.commands`,
# before `scs_cli` and `ai_lab_cli` groups were defined. So, moving this
# side-effect import to the bottom, allowing the decorators to attach the defined groups.
import exasol.nb_connector.cli.commands  # noqa: E402,F401
