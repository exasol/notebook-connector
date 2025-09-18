import click


@click.group(
    help="""Manage Application configuration data in the Secure Configuration
    Storage (SCS)."""
)
def cli():
    pass
