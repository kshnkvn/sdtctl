from abc import ABC, abstractmethod
from datetime import datetime

from sdtctl.models.system import SystemBootInfo
from sdtctl.models.systemd_unit import SystemdUnitInfo, TimerProperties
from sdtctl.models.timer import Timer


class SystemBootTimeProvider(ABC):
    """Abstract interface for system boot time providers.
    """

    @abstractmethod
    def get_boot_time(self) -> SystemBootInfo:
        """Get system boot time information.
        """


class TimeConverter(ABC):
    """Abstract interface for time conversion operations.
    """

    @abstractmethod
    def convert_monotonic_to_datetime(
        self,
        monotonic_usec: int,
        boot_info: SystemBootInfo,
    ) -> datetime:
        """Convert monotonic microseconds to absolute datetime.
        """

    @abstractmethod
    def convert_realtime_to_datetime(self, realtime_usec: int) -> datetime:
        """Convert realtime microseconds to absolute datetime.
        """


class TimerPropertiesExtractor(ABC):
    """Abstract interface for extracting timer properties from D-Bus.
    """

    @abstractmethod
    async def extract_timer_properties(
        self,
        object_path: str,
    ) -> TimerProperties:
        """Extract timer properties from D-Bus object.
        """


class TimerFactory(ABC):
    """Abstract interface for creating Timer instances.
    """

    @abstractmethod
    def create_timer(
        self,
        unit_info: SystemdUnitInfo,
        properties: TimerProperties,
    ) -> Timer:
        """Create a Timer instance from unit info and properties.
        """


class SystemdUnitParser(ABC):
    """Abstract interface for parsing systemd unit data.
    """

    @abstractmethod
    def parse_unit_list_entry(self, unit_data: list) -> SystemdUnitInfo:
        """Parse a single unit entry from D-Bus list_units response.
        """
