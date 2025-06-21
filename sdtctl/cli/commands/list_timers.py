import asyncio
from datetime import datetime

import click

from sdtctl.systemd import SystemdTimerManager, TimerInfo


def format_timer_time(dt: datetime | None) -> str:
    """Format datetime for display in timer table.
    """
    if dt is None:
        return 'N/A'

    now = datetime.now(dt.tzinfo)
    diff = dt - now

    if diff.total_seconds() < 0:
        # Past time
        diff = now - dt
        if diff.total_seconds() < 3600:
            return f'{int(diff.total_seconds() / 60)}m ago'
        elif diff.total_seconds() < 86400:
            return f'{int(diff.total_seconds() / 3600)}h ago'
        elif diff.total_seconds() < 604800:
            days = int(diff.total_seconds() / 86400)
            return f'{days}d ago'
        else:
            return dt.strftime('%Y-%m-%d')
    else:
        if diff.total_seconds() < 3600:
            return f'in {int(diff.total_seconds() / 60)}m'
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            minutes = int((diff.total_seconds() % 3600) / 60)
            return f'in {hours}h {minutes}m'
        else:
            return dt.strftime('%Y-%m-%d %H:%M')


def format_timers_table(
    timers: list[TimerInfo],
    show_full: bool = False,
) -> str:
    """Format timers into a simple table.
    """
    if not timers:
        return 'No timers found.'

    # Calculate column widths
    name_width = max(len('TIMER'), max(len(t.name) for t in timers))
    state_width = max(
        len('STATE'),
        max(len(t.active_state.value) for t in timers),
    )
    next_width = max(
        len('NEXT'),
        max(len(format_timer_time(t.next_elapse)) for t in timers),
    )
    last_width = max(
        len('LAST'),
        max(len(format_timer_time(t.last_trigger)) for t in timers),
    )

    lines = []

    if show_full:
        header = (
            f'{'TIMER':<{name_width}} '
            f'{'STATE':<{state_width}} '
            f'{'NEXT':<{next_width}} '
            f'{'LAST':<{last_width}} '
            f'DESCRIPTION'
        )
    else:
        header = (
            f'{'TIMER':<{name_width}} '
            f'{'STATE':<{state_width}} '
            f'{'NEXT':<{next_width}} '
            f'{'LAST':<{last_width}}'
        )

    lines.append(header)
    lines.append('-' * len(header))

    for timer in sorted(timers, key=lambda t: t.name):
        next_str = format_timer_time(timer.next_elapse)
        last_str = format_timer_time(timer.last_trigger)

        if show_full:
            row = (
                f'{timer.name:<{name_width}} '
                f'{timer.active_state.value:<{state_width}} '
                f'{next_str:<{next_width}} '
                f'{last_str:<{last_width}} '
                f'{timer.description}'
            )
        else:
            row = (
                f'{timer.name:<{name_width}} '
                f'{timer.active_state.value:<{state_width}} '
                f'{next_str:<{next_width}} '
                f'{last_str:<{last_width}}'
            )

        lines.append(row)

    return '\n'.join(lines)


@click.command('list-timers')
@click.option(
    '--full',
    is_flag=True,
    help='Show full information including descriptions.',
)
def list_timers(full: bool) -> None:
    """List all systemd timers.
    """
    async def _list_timers() -> None:
        try:
            manager = SystemdTimerManager()
            timers = await manager.list_timers()
            table = format_timers_table(timers, show_full=full)
            click.echo(table)
        except Exception as e:
            click.echo(f'Error: {e}', err=True)

    asyncio.run(_list_timers())
