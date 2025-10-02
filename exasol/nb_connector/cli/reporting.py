import click


def info(text: str):
    click.echo(click.style(text, fg="green"))


def success(text: str):
    click.echo(click.style(text, fg="green"))


def error(text: str | Exception):
    click.echo(click.style(f"Error: {text}", fg="bright_red"))


def warning(text: str):
    click.echo(click.style(f"Warning: {text}", fg="yellow"))
