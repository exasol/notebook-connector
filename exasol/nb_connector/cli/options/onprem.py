import click


ONPREM_OPTIONS = [
    click.option(
        "--db-host-name",
        metavar="HOST",
        type=str,
        default="localhost",
        show_default=True,
        help="Database connection host name",
    ),
    click.option(
        "--db-port",
        metavar="PORT",
        type=int,
        default=8563,
        show_default=True,
        help="Database connection port",
    ),
    click.option(
        "--db-username",
        metavar="USERNAME",
        type=str,
        help="Database user name",
    ),
    click.option(
        "--db-password",
        metavar="PASSWORD",
        type=str,
        prompt=True,
        prompt_required=False,
        # show_envvar=True,
        hide_input=True,
        help="Database password",
    ),
    click.option(
        "--db-use-encryption/--no-db-use-encryption",
        type=bool,
        default=True,
        show_default=True,
        help="Whether to encrypt communication with the database or not",
    ),
]
