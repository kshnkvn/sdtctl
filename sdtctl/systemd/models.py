import re
from datetime import datetime
from pathlib import Path
from typing import Any, Self

from dbus_next.signature import Variant
from pydantic import Field, field_validator, model_validator

from sdtctl.systemd.types import (
    TimerOperation,
    UnitActiveState,
    UnitFileState,
    UnitLoadState,
)
from sdtctl.utils import BaseModel


class TimerInfo(BaseModel):
    """Information about a systemd timer.

    Args:
        name: Timer unit name
        description: Timer description
        active_state: Current active state
        load_state: Current load state
        file_state: Unit file state
        next_elapse: Next scheduled execution time
        last_trigger: Last trigger time
        object_path: D-Bus object path
    """
    model_config = {'frozen': True}

    name: str = Field(..., min_length=1)
    description: str = Field(...)
    active_state: UnitActiveState = Field(...)
    load_state: UnitLoadState = Field(...)
    file_state: UnitFileState = Field(...)
    next_elapse: datetime | None = Field(None)
    last_trigger: datetime | None = Field(None)
    object_path: str = Field(...)

    @field_validator('object_path')
    @classmethod
    def validate_object_path(cls, v: str) -> str:
        if not v.startswith('/'):
            raise ValueError('Object path must start with /')
        return v


class TimerOperationResult(BaseModel):
    """Result of a timer operation.

    Args:
        success: Whether the operation was successful
        timer_name: Name of the timer
        operation: Type of operation performed
        message: Operation result message
        job_path: D-Bus job path
    """
    model_config = {'frozen': True}

    success: bool = Field(...)
    timer_name: str = Field(..., min_length=1)
    operation: TimerOperation = Field(...)
    message: str = Field('', max_length=1000)
    job_path: str = Field('')


class TimerCreationRequest(BaseModel):
    """Request for creating a new timer.

    Args:
        name: Timer name
        description: Timer description
        command: Command to execute
        calendar_spec: Calendar specification (e.g., "daily", "00:30:00")
        on_boot_sec: Seconds after boot
        on_startup_sec: Seconds after startup
        on_unit_active_sec: Seconds after unit becomes active
        on_unit_inactive_sec: Seconds after unit becomes inactive
        user: User to run service as
        working_directory: Working directory
        environment: Environment variables
        persistent: Timer persists across reboots
        wake_system: Timer can wake system from sleep
        accuracy_sec: Timer accuracy in seconds
        randomized_delay_sec: Random delay in seconds
    """
    model_config = {'frozen': True}

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    calendar_spec: str | None = Field(None)
    on_boot_sec: int | None = Field(None, ge=0)
    on_startup_sec: int | None = Field(None, ge=0)
    on_unit_active_sec: int | None = Field(None, ge=0)
    on_unit_inactive_sec: int | None = Field(None, ge=0)
    user: str | None = Field(None)
    working_directory: str | None = Field(None)
    environment: dict[str, str] = Field(default_factory=dict)
    persistent: bool = Field(False)
    wake_system: bool = Field(False)
    accuracy_sec: int = Field(60, ge=0)
    randomized_delay_sec: int = Field(0, ge=0)

    @field_validator('name')
    @classmethod
    def validate_timer_name(cls, v: str) -> str:
        # Remove .timer suffix if present for validation
        base_name = v.removesuffix('.timer')

        # Systemd unit name validation
        if not re.match(r'^[a-zA-Z0-9:_.\\-]+$', base_name):
            raise ValueError(
                'Timer name contains invalid characters. '
                'Use only letters, numbers, :, _, ., \\, -'
            )

        if base_name.startswith('.') or base_name.endswith('.'):
            raise ValueError('Timer name cannot start or end with a dot')

        return v

    @field_validator('working_directory')
    @classmethod
    def validate_working_directory(cls, v: str | None) -> str | None:
        if v is not None:
            path = Path(v)
            if not path.exists():
                raise ValueError(f'Working directory does not exist: {v}')
            if not path.is_dir():
                raise ValueError(f'Working directory is not a directory: {v}')
        return v

    @model_validator(mode='after')
    def validate_at_least_one_schedule(self) -> 'TimerCreationRequest':
        if not any([
            self.calendar_spec,
            self.on_boot_sec,
            self.on_startup_sec,
            self.on_unit_active_sec,
            self.on_unit_inactive_sec
        ]):
            raise ValueError('At least one schedule type must be specified')
        return self


class TimerCreationResult(BaseModel):
    """Result of timer creation.

    Args:
        success: Whether the timer was created successfully
        timer_name: Name of the created timer
        timer_path: Path to the timer unit file
        service_path: Path to the service unit file
        enabled: Whether the timer was enabled after creation
        error_message: Error message if creation failed
    """
    model_config = {'frozen': True}

    success: bool = Field(...)
    timer_name: str = Field(..., min_length=1)
    timer_path: Path | None = Field(None)
    service_path: Path | None = Field(None)
    enabled: bool = Field(False)
    error_message: str = Field('', max_length=1000)


class TimerPreview(BaseModel):
    """Preview of timer unit files before creation.

    Args:
        timer_content: Timer unit file content
        service_content: Service unit file content
        timer_path: Path where timer unit file will be created
        service_path: Path where service unit file will be created
    """
    model_config = {'frozen': True}

    timer_content: str = Field(..., min_length=1)
    service_content: str = Field(..., min_length=1)
    timer_path: Path = Field(...)
    service_path: Path = Field(...)


class DBusTimerProperties(BaseModel):
    """Raw D-Bus timer properties.

    Args:
        next_elapse_realtime_usec: Next elapse time (realtime, microseconds)
        next_elapse_monotonic_usec: Next elapse time (monotonic, microseconds)
        last_trigger_usec: Last trigger time (microseconds)
        result: Timer result
        accuracy_usec: Timer accuracy in microseconds
        randomized_delay_usec: Random delay in microseconds
        persistent: Timer persists across reboots
        wake_system: Timer can wake system from sleep
        remain_after_elapse: Timer remains after elapsing
    """
    model_config = {'frozen': True}

    next_elapse_realtime_usec: int = Field(..., ge=0)
    next_elapse_monotonic_usec: int = Field(..., ge=0)
    last_trigger_usec: int | None = Field(None, ge=0)
    result: str | None = Field(None)
    accuracy_usec: int = Field(..., ge=0)
    randomized_delay_usec: int = Field(..., ge=0)
    persistent: bool = Field(...)
    wake_system: bool = Field(...)
    remain_after_elapse: bool = Field(...)


class DBusUnitData(BaseModel):
    """Raw D-Bus unit data from list_units.

    Args:
        name: Unit name
        description: Unit description
        load_state: Load state
        active_state: Active state
        sub_state: Sub state
        following: Following unit
        object_path: D-Bus object path
        job_id: Job ID
        job_type: Job type
        job_object_path: Job object path
    """
    model_config = {'frozen': True}

    name: str = Field(..., min_length=1)
    description: str = Field(...)
    load_state: str = Field(...)
    active_state: str = Field(...)
    sub_state: str = Field(...)
    following: str = Field(...)
    object_path: str = Field(...)
    job_id: int = Field(..., ge=0)
    job_type: str = Field(...)
    job_object_path: str = Field(...)

    @field_validator('object_path')
    @classmethod
    def validate_object_path(cls, v: str) -> str:
        if not v.startswith('/'):
            raise ValueError('Object path must start with /')
        return v


class DBusVariantValue(BaseModel):
    """Wrapper for D-Bus variant values.

    Args:
        value: The wrapped D-Bus variant value
    """
    model_config = {'frozen': True, 'arbitrary_types_allowed': True}

    value: Any = Field(...)

    @classmethod
    def from_dbus_variant(cls, variant: Variant | Any | None) -> Self:
        """Create instance from D-Bus variant.

        Args:
            variant: The D-Bus variant to extract value from

        Returns:
            DBusVariantValue instance with extracted value
        """
        if variant and hasattr(variant, 'value'):
            return cls(value=variant.value)
        return cls(value=variant if variant is not None else 0)

    @staticmethod
    def to_dbus_variant(value: Any, signature: str = 'v') -> Variant:
        """Convert a Python value to a D-Bus variant.

        Args:
            value: The Python value to convert
            signature: The D-Bus signature (default: 'v' for variant)

        Returns:
            D-Bus Variant object
        """
        if signature == 'v':
            return Variant('v', value)
        return Variant(signature, value)


class SystemdUnitInfo(BaseModel):
    """Raw systemd unit information from D-Bus list_units call.

    Args:
        name: Unit name
        description: Unit description
        load_state: Load state
        active_state: Active state
        sub_state: Sub state
        following: Following unit
        object_path: D-Bus object path
        job_id: Job ID
        job_type: Job type
        job_object_path: Job object path
    """
    model_config = {'frozen': True}

    name: str = Field(...)
    description: str = Field(...)
    load_state: str = Field(...)
    active_state: str = Field(...)
    sub_state: str = Field(...)
    following: str = Field(...)
    object_path: str = Field(...)
    job_id: int = Field(...)
    job_type: str = Field(...)
    job_object_path: str = Field(...)


class TimerProperties(BaseModel):
    """Timer-specific D-Bus properties.

    Args:
        next_elapse_realtime_usec: Next elapse time (realtime, microseconds)
        next_elapse_monotonic_usec: Next elapse time (monotonic, microseconds)
        last_trigger_usec: Last trigger time (microseconds)
        result: Timer result
    """
    model_config = {'frozen': True}

    next_elapse_realtime_usec: int = Field(..., ge=0)
    next_elapse_monotonic_usec: int = Field(..., ge=0)
    last_trigger_usec: int | None = Field(None, ge=0)
    result: str | None = Field(None)
