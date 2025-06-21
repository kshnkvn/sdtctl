import click

from sdtctl.cli.commands.list_timers import list_timers


@click.group()
def cli() -> None:
    """sdtctl - Manage systemd timers.
    """
    pass


def run_cli() -> None:
    """Run the CLI interface.
    """
    cli.add_command(list_timers)

    cli()


__all__ = [
    'cli',
    'run_cli',
]
