from datetime import datetime

from sdtctl.dbus.interfaces import TimeConverter
from sdtctl.models.system import SystemBootInfo


class StandardTimeConverter(TimeConverter):
    """Standard implementation of time conversion operations.
    """

    def convert_realtime_to_datetime(self, realtime_usec: int) -> datetime:
        """Convert realtime microseconds to absolute datetime.
        """
        return datetime.fromtimestamp(realtime_usec / 1_000_000)

    def convert_monotonic_to_datetime(
        self, monotonic_usec: int, boot_info: SystemBootInfo
    ) -> datetime:
        """Convert monotonic microseconds to absolute datetime.
        """
        absolute_timestamp = boot_info.boot_time_seconds + (
            monotonic_usec / 1_000_000
        )
        return datetime.fromtimestamp(absolute_timestamp)
