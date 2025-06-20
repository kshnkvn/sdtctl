from datetime import datetime

from pydantic import BaseModel, Field


class Timer(BaseModel):
    """Represents a systemd timer.
    """
    model_config = {'frozen': True}

    name: str = Field(..., description='Timer unit name')
    active_state: str = Field(..., description='Current active state')
    next_elapse: datetime | None = Field(
        None,
        description='Next scheduled execution time',
    )
