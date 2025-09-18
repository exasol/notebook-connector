import click

SAAS_OPTIONS = [
    click.option(
        "--saas-url",
        metavar="URL",
        type=str,
        default="https://cloud.exasol.com",
        show_default=True,
        help="SaaS service URL",
    ),
    click.option(
        "--saas-account-id",
        metavar="ACCOUNT_ID",
        type=str,
        help="SaaS account ID",
    ),
    click.option(
        "--saas-database-id",
        metavar="ID",
        type=str,
        help="SaaS database ID",
    ),
    click.option(
        "--saas-database-name",
        metavar="NAME",
        type=str,
        help="SaaS database name",
    ),
    click.option(
        "--saas-token",
        metavar="PAT",
        type=str,
        prompt=True,
        hide_input=True,
        help="SaaS personal access token",
    ),
]
