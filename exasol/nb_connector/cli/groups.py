import click


@click.group()
def cli():
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
