from sdtctl.dbus.interfaces import SystemBootTimeProvider
from sdtctl.models.system import SystemBootInfo


class ProcSystemBootTimeProvider(SystemBootTimeProvider):
    """System boot time provider using /proc filesystem.
    """

    def get_boot_time(self) -> SystemBootInfo:
        """Get system boot time from /proc/stat with fallback.
        """
        try:
            return SystemBootInfo.from_proc_stat()
        except RuntimeError:
            return SystemBootInfo.from_proc_uptime_fallback()
