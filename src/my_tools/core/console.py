import click


def notice(message: str):
    click.secho(message, fg="green")


def warn(message: str):
    click.secho(message, fg="yellow")


def error(message: str, exit_code: int = 1):
    click.secho(message, fg="red", err=True)
    raise click.exceptions.Exit(exit_code)


def confirm(message: str, default: bool = True) -> bool:
    return click.confirm(message, default=default)
