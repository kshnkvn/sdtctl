import re
import shlex
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


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
    """Represents a timer schedule configuration.
    """
    model_config = {'frozen': True}

    # Calendar-based schedules (OnCalendar)
    calendar_spec: str | None = Field(
        None,
        description='Calendar specification (e.g., "daily", "00:30:00")',
    )

    # Monotonic schedules
    on_boot_sec: int | None = Field(
        None,
        ge=0,
        description='Seconds after boot',
    )
    on_startup_sec: int | None = Field(
        None,
        ge=0,
        description='Seconds after startup',
    )
    on_unit_active_sec: int | None = Field(
        None,
        ge=0,
        description='Seconds after unit becomes active',
    )
    on_unit_inactive_sec: int | None = Field(
        None,
        ge=0,
        description='Seconds after unit becomes inactive',
    )

    # Timer behavior
    accuracy_sec: int = Field(
        60,
        ge=0,
        description='Timer accuracy in seconds',
    )
    randomized_delay_sec: int = Field(
        0,
        ge=0,
        description='Random delay in seconds',
    )
    persistent: bool = Field(
        False,
        description='Timer persists across reboots',
    )
    wake_system: bool = Field(
        False,
        description='Timer can wake system from sleep',
    )
    remain_after_elapse: bool = Field(
        True,
        description='Timer remains after elapsing',
    )

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
    """
    model_config = {'frozen': True}

    exec_start: str = Field(
        ...,
        min_length=1,
        description='Command to execute',
    )
    user: str | None = Field(
        None,
        description='User to run service as',
    )
    group: str | None = Field(
        None,
        description='Group to run service as',
    )
    working_directory: Path | None = Field(
        None,
        description='Working directory',
    )
    environment: dict[str, str] | None = Field(
        None,
        description='Environment variables',
    )
    type: ServiceType = Field(
        ServiceType.ONESHOT,
        description='Service type',
    )
    restart: RestartPolicy = Field(
        RestartPolicy.NO,
        description='Restart policy',
    )

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
    """
    model_config = {'frozen': True}

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description='Timer name',
    )
    description: str = Field(
        ...,
        min_length=1,
        description='Timer description',
    )
    timer_schedule: TimerSchedule
    service_config: ServiceConfig
    enabled: bool = Field(
        True,
        description='Enable timer after creation',
    )

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
    """
    model_config = {'frozen': True}

    success: bool = Field(
        ...,
        description='Whether the timer was created successfully',
    )
    timer_name: str = Field(
        ...,
        description='Name of the created timer',
    )
    service_name: str = Field(
        ...,
        description='Name of the created service',
    )
    message: str = Field(
        ...,
        description='Success or error message',
    )
    enabled: bool = Field(
        False,
        description='Whether the timer was enabled after creation',
    )
