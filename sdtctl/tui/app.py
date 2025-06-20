from textual.app import App

from sdtctl.dbus.connection import DBusConnectionManager
from sdtctl.tui.screens.timer_list import TimerListScreen


class SdtctlApp(App[None]):
    """A textual application to manage systemd timers.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the app with the D-Bus connection manager.
        """
        super().__init__(*args, **kwargs)
        self._dbus_manager = DBusConnectionManager.get_instance()

    async def on_mount(self) -> None:
        """Mount the main screen and connect to D-Bus.
        """
        await self._dbus_manager.connect()
        self.push_screen(TimerListScreen())
