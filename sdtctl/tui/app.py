from textual.app import App

from sdtctl.tui.screens.timer_list import TimerListScreen


class SdtctlApp(App[None]):
    """A textual application to manage systemd timers.
    """

    def on_mount(self) -> None:
        """Mount the main screen.
        """
        self.push_screen(TimerListScreen())
