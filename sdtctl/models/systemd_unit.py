from pydantic import BaseModel, Field


class SystemdUnitInfo(BaseModel):
    """Raw systemd unit information from D-Bus list_units call.
    """
    model_config = {'frozen': True}

    name: str = Field(..., description='Unit name')
    description: str = Field(..., description='Unit description')
    load_state: str = Field(..., description='Load state')
    active_state: str = Field(..., description='Active state')
    sub_state: str = Field(..., description='Sub state')
    following: str = Field(..., description='Following unit')
    object_path: str = Field(..., description='D-Bus object path')
    job_id: int = Field(..., description='Job ID')
    job_type: str = Field(..., description='Job type')
    job_object_path: str = Field(..., description='Job object path')


class TimerProperties(BaseModel):
    """Timer-specific D-Bus properties.
    """
    model_config = {'frozen': True}

    next_elapse_realtime_usec: int = Field(
        ...,
        ge=0,
        description='Next elapse time (realtime, microseconds)',
    )
    next_elapse_monotonic_usec: int = Field(
        ...,
        ge=0,
        description='Next elapse time (monotonic, microseconds)',
    )
    last_trigger_usec: int | None = Field(
        None,
        ge=0,
        description='Last trigger time (microseconds)',
    )
    result: str | None = Field(
        None,
        description='Timer result',
    )
