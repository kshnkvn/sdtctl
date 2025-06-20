from enum import StrEnum
from typing import Final


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
    UNIT_INTERFACE = 'org.freedesktop.systemd1.Unit'
    SERVICE_INTERFACE = 'org.freedesktop.systemd1.Service'
    TIMER_INTERFACE = 'org.freedesktop.systemd1.Timer'
    TARGET_INTERFACE = 'org.freedesktop.systemd1.Target'
    SOCKET_INTERFACE = 'org.freedesktop.systemd1.Socket'
    DEVICE_INTERFACE = 'org.freedesktop.systemd1.Device'
    MOUNT_INTERFACE = 'org.freedesktop.systemd1.Mount'
    AUTOMOUNT_INTERFACE = 'org.freedesktop.systemd1.Automount'
    SWAP_INTERFACE = 'org.freedesktop.systemd1.Swap'
    PATH_INTERFACE = 'org.freedesktop.systemd1.Path'
    SLICE_INTERFACE = 'org.freedesktop.systemd1.Slice'
    SCOPE_INTERFACE = 'org.freedesktop.systemd1.Scope'

    # Unit file suffixes
    TIMER_SUFFIX = '.timer'
    SERVICE_SUFFIX = '.service'
    TARGET_SUFFIX = '.target'
    SOCKET_SUFFIX = '.socket'
    DEVICE_SUFFIX = '.device'
    MOUNT_SUFFIX = '.mount'
    AUTOMOUNT_SUFFIX = '.automount'
    SWAP_SUFFIX = '.swap'
    PATH_SUFFIX = '.path'
    SLICE_SUFFIX = '.slice'
    SCOPE_SUFFIX = '.scope'


class UnitPropertyNames(StrEnum):
    """Systemd unit property names for the Unit interface.
    """

    # Basic unit information
    ID = 'Id'
    NAMES = 'Names'
    DESCRIPTION = 'Description'
    LOAD_STATE = 'LoadState'
    ACTIVE_STATE = 'ActiveState'
    SUB_STATE = 'SubState'
    FOLLOWING = 'Following'
    UNIT_FILE_STATE = 'UnitFileState'
    UNIT_FILE_PRESET = 'UnitFilePreset'

    # Job information
    JOB = 'Job'

    # Unit relationships
    REQUIRES = 'Requires'
    REQUISITE = 'Requisite'
    WANTS = 'Wants'
    BINDS_TO = 'BindsTo'
    PART_OF = 'PartOf'
    REQUIRED_BY = 'RequiredBy'
    REQUISITE_OF = 'RequisiteOf'
    WANTED_BY = 'WantedBy'
    BOUND_BY = 'BoundBy'
    CONSISTS_OF = 'ConsistsOf'
    CONFLICTS = 'Conflicts'
    CONFLICTED_BY = 'ConflictedBy'
    BEFORE = 'Before'
    AFTER = 'After'

    # Conditions and assertions
    CONDITION_RESULT = 'ConditionResult'
    ASSERT_RESULT = 'AssertResult'

    # Timestamps
    CONDITION_TIMESTAMP = 'ConditionTimestamp'
    CONDITION_TIMESTAMP_MONOTONIC = 'ConditionTimestampMonotonic'
    ASSERT_TIMESTAMP = 'AssertTimestamp'
    ASSERT_TIMESTAMP_MONOTONIC = 'AssertTimestampMonotonic'
    INACTIVE_EXIT_TIMESTAMP = 'InactiveExitTimestamp'
    INACTIVE_EXIT_TIMESTAMP_MONOTONIC = 'InactiveExitTimestampMonotonic'
    ACTIVE_ENTER_TIMESTAMP = 'ActiveEnterTimestamp'
    ACTIVE_ENTER_TIMESTAMP_MONOTONIC = 'ActiveEnterTimestampMonotonic'
    ACTIVE_EXIT_TIMESTAMP = 'ActiveExitTimestamp'
    ACTIVE_EXIT_TIMESTAMP_MONOTONIC = 'ActiveExitTimestampMonotonic'
    INACTIVE_ENTER_TIMESTAMP = 'InactiveEnterTimestamp'
    INACTIVE_ENTER_TIMESTAMP_MONOTONIC = 'InactiveEnterTimestampMonotonic'


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
    FIXED_RANDOM_DELAY = 'FixedRandomDelay'
    PERSISTENT = 'Persistent'
    WAKE_SYSTEM = 'WakeSystem'
    REMAIN_AFTER_ELAPSE = 'RemainAfterElapse'

    # Timer specifications
    TIMER_SPECS = 'TimersMonotonic'
    TIMER_SPECS_CALENDAR = 'TimersCalendar'


class UnitControlModes(StrEnum):
    """Systemd unit control mode constants.
    """

    REPLACE = 'replace'
    FAIL = 'fail'
    ISOLATE = 'isolate'
    IGNORE_DEPENDENCIES = 'ignore-dependencies'
    IGNORE_REQUIREMENTS = 'ignore-requirements'


class UnitFileStates(StrEnum):
    """Systemd unit file state constants.
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


class UnitActiveStates(StrEnum):
    """Systemd unit active state constants.
    """

    ACTIVE = 'active'
    RELOADING = 'reloading'
    INACTIVE = 'inactive'
    FAILED = 'failed'
    ACTIVATING = 'activating'
    DEACTIVATING = 'deactivating'


class UnitLoadStates(StrEnum):
    """Systemd unit load state constants.
    """

    LOADED = 'loaded'
    ERROR = 'error'
    NOT_FOUND = 'not-found'
    BAD_SETTING = 'bad-setting'
    MERGED = 'merged'
    MASKED = 'masked'


class ConnectionConfig:
    """Configuration constants for D-Bus connection.
    """

    DEFAULT_MAX_RETRIES: Final[int] = 5
    DEFAULT_INITIAL_BACKOFF: Final[float] = 1.0
    BACKOFF_MULTIPLIER: Final[float] = 2.0
