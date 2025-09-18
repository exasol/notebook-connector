import click

SSL_OPTIONS = [
    click.option(
        "--ssl-use-cert-validation/--no-ssl-use-cert-validation",
        type=bool,
        default=True,
        show_default=True,
        help="Whether to validate SSL certificates or not",
    ),
    click.option(
        "--ssl-cert-path",
        metavar="FILE/DIR",
        type=str,
        help="SSL trusted CA file/dir",
    ),
 ]
