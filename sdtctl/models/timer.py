from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Timer:
    """A dataclass to represent a systemd timer.
    """

    name: str
    active_state: str
    next_elapse: datetime | None
