from sdtctl.dbus.systemd import SystemdDBusService
from sdtctl.models.timer import Timer


class TimerService:
    """A service for managing systemd timers.
    """

    def __init__(self) -> None:
        """Initialise the service.
        """
        self._dbus_service = SystemdDBusService()

    async def get_timers(self) -> list[Timer]:
        """Get a list of all systemd timers.
        """
        await self._dbus_service.connect()
        return await self._dbus_service.list_timers()
