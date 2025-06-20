from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Self


class DBusConstants(StrEnum):
    """D-Bus service and interface constants.
    """

    DBUS_SERVICE_NAME = 'org.freedesktop.DBus'
    DBUS_OBJECT_PATH = '/org/freedesktop/DBus'
    DBUS_INTERFACE = 'org.freedesktop.DBus'


class SystemdDBusConstants(StrEnum):
    """Systemd D-Bus service constants.
    """

    BUS_NAME = 'org.freedesktop.systemd1'
    BUS_PATH = '/org/freedesktop/systemd1'
    MANAGER_INTERFACE = 'org.freedesktop.systemd1.Manager'
    TIMER_SUFFIX = '.timer'


class ConnectionConfig:
    """Configuration constants for D-Bus connection.
    """

    DEFAULT_MAX_RETRIES: Final[int] = 5
    DEFAULT_INITIAL_BACKOFF: Final[float] = 1.0
    BACKOFF_MULTIPLIER: Final[float] = 2.0


@dataclass(frozen=True)
class DBusVariantValue:
    """Wrapper for D-Bus variant values.
    """

    value: int

    @classmethod
    def from_dbus_variant(cls, variant) -> Self:
        """Create instance from D-Bus variant.
        """
        if variant and hasattr(variant, 'value'):
            return cls(value=variant.value)
        return cls(value=0)
