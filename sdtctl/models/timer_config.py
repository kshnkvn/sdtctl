import re
import shlex
from enum import StrEnum
from pathlib import Path

from pydantic import Field, field_validator, model_validator

from sdtctl.utils import BaseModel


class ServiceType(StrEnum):
    SIMPLE = 'simple'
    EXEC = 'exec'
    FORKING = 'forking'
    ONESHOT = 'oneshot'
    DBUS = 'dbus'
    NOTIFY = 'notify'
    IDLE = 'idle'


class RestartPolicy(StrEnum):
    NO = 'no'
    ALWAYS = 'always'
    ON_SUCCESS = 'on-success'
    ON_FAILURE = 'on-failure'
    ON_ABNORMAL = 'on-abnormal'
    ON_ABORT = 'on-abort'
    ON_WATCHDOG = 'on-watchdog'


class TimerSchedule(BaseModel):
    """Timer schedule configuration.

    Args:
        calendar_spec: Calendar specification (e.g., "daily", "00:30:00")
        on_boot_sec: Seconds after boot
        on_startup_sec: Seconds after startup
        on_unit_active_sec: Seconds after unit becomes active
        on_unit_inactive_sec: Seconds after unit becomes inactive
        accuracy_sec: Timer accuracy in seconds
        randomized_delay_sec: Random delay in seconds
        persistent: Timer persists across reboots
        wake_system: Timer can wake system from sleep
        remain_after_elapse: Timer remains after elapsing
    """
    model_config = {'frozen': True}

    calendar_spec: str | None = Field(None)
    on_boot_sec: int | None = Field(None, ge=0)
    on_startup_sec: int | None = Field(None, ge=0)
    on_unit_active_sec: int | None = Field(None, ge=0)
    on_unit_inactive_sec: int | None = Field(None, ge=0)
    accuracy_sec: int = Field(60, ge=0)
    randomized_delay_sec: int = Field(0, ge=0)
    persistent: bool = Field(False)
    wake_system: bool = Field(False)
    remain_after_elapse: bool = Field(True)

    @field_validator('calendar_spec')
    @classmethod
    def validate_calendar_spec(cls, v: str | None) -> str | None:
        if v is not None:
            if not v.strip():
                raise ValueError('Calendar specification cannot be empty')
            if v.count(':') > 2:
                raise ValueError(
                    'Invalid time format in calendar specification'
                )
        return v

    @model_validator(mode='after')
    def validate_at_least_one_schedule(self) -> 'TimerSchedule':
        if not any([
            self.calendar_spec,
            self.on_boot_sec,
            self.on_startup_sec,
            self.on_unit_active_sec,
            self.on_unit_inactive_sec
        ]):
            raise ValueError('At least one schedule type must be specified')
        return self


class ServiceConfig(BaseModel):
    """Configuration for the service unit that the timer triggers.

    Args:
        exec_start: Command to execute
        user: User to run service as
        group: Group to run service as
        working_directory: Working directory
        environment: Environment variables
        type: Service type
        restart: Restart policy
    """
    model_config = {'frozen': True}

    exec_start: str = Field(..., min_length=1)
    user: str | None = Field(None)
    group: str | None = Field(None)
    working_directory: Path | None = Field(None)
    environment: dict[str, str] | None = Field(None)
    type: ServiceType = Field(ServiceType.ONESHOT)
    restart: RestartPolicy = Field(RestartPolicy.NO)

    @field_validator('exec_start')
    @classmethod
    def validate_command(cls, v: str) -> str:
        try:
            shlex.split(v)
        except ValueError as e:
            raise ValueError(f'Invalid command format: {e}')
        return v

    @field_validator('working_directory')
    @classmethod
    def validate_working_directory(cls, v: Path | None) -> Path | None:
        if v is not None and not v.is_dir():
            raise ValueError(f'Working directory does not exist: {v}')
        return v


class TimerCreationConfig(BaseModel):
    """Complete configuration for creating a new timer.

    Args:
        name: Timer name
        description: Timer description
        timer_schedule: Timer schedule configuration
        service_config: Service configuration
        enabled: Enable timer after creation
    """
    model_config = {'frozen': True}

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    timer_schedule: TimerSchedule
    service_config: ServiceConfig
    enabled: bool = Field(True)

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


class CreateTimerResult(BaseModel):
    """Result of timer creation operation.

    Args:
        success: Whether the timer was created successfully
        timer_name: Name of the created timer
        service_name: Name of the created service
        message: Success or error message
        enabled: Whether the timer was enabled after creation
    """
    model_config = {'frozen': True}

    success: bool = Field(...)
    timer_name: str = Field(...)
    service_name: str = Field(...)
    message: str = Field(...)
    enabled: bool = Field(False)
