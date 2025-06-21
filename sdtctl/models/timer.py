from datetime import datetime

from pydantic import Field

from sdtctl.utils import BaseModel


class Timer(BaseModel):
    """Systemd timer.

    Args:
        name: Timer unit name
        active_state: Current active state
        next_elapse: Next scheduled execution time
    """
    model_config = {'frozen': True}

    name: str = Field(...)
    active_state: str = Field(...)
    next_elapse: datetime | None = Field(None)
