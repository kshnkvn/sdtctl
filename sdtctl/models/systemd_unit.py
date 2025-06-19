from dataclasses import dataclass


@dataclass(frozen=True)
class SystemdUnitInfo:
    """Raw systemd unit information from D-Bus list_units call.
    """

    name: str
    description: str
    load_state: str
    active_state: str
    sub_state: str
    following: str
    object_path: str
    job_id: int
    job_type: str
    job_object_path: str


@dataclass(frozen=True)
class TimerProperties:
    """Timer-specific D-Bus properties.
    """

    next_elapse_realtime_usec: int
    next_elapse_monotonic_usec: int
    last_trigger_usec: int | None = None
    result: str | None = None
