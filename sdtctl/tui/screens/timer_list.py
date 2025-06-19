from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable

from sdtctl.services.timer_service import TimerService


class TimerListScreen(Screen):
    """A screen to display a list of systemd timers.
    """

    def __init__(self) -> None:
        """Initialise the screen.
        """
        super().__init__()
        self._timer_service = TimerService()
        self._timers_table = DataTable()

    def compose(self) -> ComposeResult:
        """Compose the screen.
        """
        yield self._timers_table

    async def on_mount(self) -> None:
        """Mount the screen.
        """
        self._timers_table.add_column('Name')
        self._timers_table.add_column('Next Elapse')
        self._timers_table.add_column('Active State')

        timers = await self._timer_service.get_timers()
        for timer in timers:
            # Format the next elapse time without microseconds
            # for cleaner display
            next_elapse_str = 'Not scheduled'
            if timer.next_elapse:
                # Format without microseconds: YYYY-MM-DD HH:MM:SS
                next_elapse_str = timer.next_elapse.strftime(
                    '%Y-%m-%d %H:%M:%S'
                )

            self._timers_table.add_row(
                timer.name,
                next_elapse_str,
                timer.active_state,
            )
