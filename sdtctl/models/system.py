import time
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class SystemBootInfo:
    """System boot time information.
    """

    boot_time_seconds: int

    @classmethod
    def from_proc_stat(cls) -> Self:
        """Read boot time from /proc/stat.
        """
        try:
            with open('/proc/stat') as f:
                for line in f:
                    if line.startswith('btime '):
                        boot_time = int(line.split()[1])
                        return cls(boot_time_seconds=boot_time)
        except (OSError, IndexError, ValueError) as e:
            raise RuntimeError(
                f'Failed to read boot time from /proc/stat: {e}'
            )

        raise RuntimeError('Boot time not found in /proc/stat')

    @classmethod
    def from_proc_uptime_fallback(cls) -> Self:
        """Fallback method using /proc/uptime.
        """
        try:
            with open('/proc/uptime') as uptime_file:
                uptime_seconds = float(uptime_file.read().split()[0])
                boot_time = int(time.time() - uptime_seconds)
                return cls(boot_time_seconds=boot_time)
        except (OSError, IndexError, ValueError) as e:
            raise RuntimeError(
                f'Failed to read uptime from /proc/uptime: {e}'
            )
