from enum import StrEnum
from typing import Final


class TimerOperation(StrEnum):
    """Timer operation types.
    """

    START = 'start'
    STOP = 'stop'
    RESTART = 'restart'
    ENABLE = 'enable'
    DISABLE = 'disable'
    DELETE = 'delete'


class UnitFileState(StrEnum):
    """Systemd unit file states.
    """

    ENABLED = 'enabled'
    ENABLED_RUNTIME = 'enabled-runtime'
    LINKED = 'linked'
    LINKED_RUNTIME = 'linked-runtime'
    MASKED = 'masked'
    MASKED_RUNTIME = 'masked-runtime'
    STATIC = 'static'
    DISABLED = 'disabled'
    INVALID = 'invalid'


class UnitActiveState(StrEnum):
    """Systemd unit active states.
    """

    ACTIVE = 'active'
    RELOADING = 'reloading'
    INACTIVE = 'inactive'
    FAILED = 'failed'
    ACTIVATING = 'activating'
    DEACTIVATING = 'deactivating'


class UnitLoadState(StrEnum):
    """Systemd unit load states.
    """

    LOADED = 'loaded'
    ERROR = 'error'
    NOT_FOUND = 'not-found'
    BAD_SETTING = 'bad-setting'
    MERGED = 'merged'
    MASKED = 'masked'


class DBusConstants(StrEnum):
    """Standard D-Bus service and interface constants.
    """

    # D-Bus daemon service constants
    SERVICE_NAME = 'org.freedesktop.DBus'
    OBJECT_PATH = '/org/freedesktop/DBus'
    INTERFACE = 'org.freedesktop.DBus'

    # Standard D-Bus interface for properties access
    PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'


class SystemdDBusConstants(StrEnum):
    """Systemd D-Bus service and interface constants.
    """

    # Service identification
    SERVICE_NAME = 'org.freedesktop.systemd1'
    OBJECT_PATH = '/org/freedesktop/systemd1'

    # Core systemd interfaces
    MANAGER_INTERFACE = 'org.freedesktop.systemd1.Manager'
    TIMER_INTERFACE = 'org.freedesktop.systemd1.Timer'

    # Unit file suffixes
    TIMER_SUFFIX = '.timer'


class TimerPropertyNames(StrEnum):
    """Systemd timer property names for the Timer interface.
    """

    # Timer schedule information
    NEXT_ELAPSE_REALTIME_USEC = 'NextElapseUSecRealtime'
    NEXT_ELAPSE_MONOTONIC_USEC = 'NextElapseUSecMonotonic'
    LAST_TRIGGER_USEC = 'LastTriggerUSec'

    # Timer configuration
    RESULT = 'Result'
    ACCURACY_USEC = 'AccuracyUSec'
    RANDOMIZED_DELAY_USEC = 'RandomizedDelayUSec'
    PERSISTENT = 'Persistent'
    WAKE_SYSTEM = 'WakeSystem'
    REMAIN_AFTER_ELAPSE = 'RemainAfterElapse'


class UnitControlModes(StrEnum):
    """Systemd unit control mode constants.
    """

    REPLACE = 'replace'


class ConnectionConfig:
    """Configuration constants for D-Bus connection."""

    DEFAULT_MAX_RETRIES: Final[int] = 5
    DEFAULT_INITIAL_BACKOFF: Final[float] = 1.0
    BACKOFF_MULTIPLIER: Final[float] = 2.0
