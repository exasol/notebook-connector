import click


COMMON_OPTIONS = [
    click.option(
        "--db-schema",
        metavar="DB_SCHEMA",
        type=str,
        help="Database schema for installing UDFs of Exasol extensions",
    )
]
