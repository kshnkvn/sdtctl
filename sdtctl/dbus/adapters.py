from datetime import datetime

from sdtctl.dbus.constants import SystemdDBusConstants, UnitPropertyNames
from sdtctl.dbus.interfaces import SystemdUnitParser, TimerFactory
from sdtctl.dbus.unit import SystemdUnit
from sdtctl.models.systemd_unit import SystemdUnitInfo, TimerProperties
from sdtctl.models.timer import Timer


class SystemdUnitInfoFactory:
    """Factory for creating SystemdUnitInfo instances from SystemdUnit objects.
    """

    @staticmethod
    async def create_from_systemd_unit(unit: SystemdUnit) -> SystemdUnitInfo:
        """Create SystemdUnitInfo from a SystemdUnit instance.

        Args:
            unit: SystemdUnit instance to extract information from

        Returns:
            SystemdUnitInfo with actual unit properties

        Raises:
            DBusError: If D-Bus calls fail
        """
        # Get unit properties directly from the SystemdUnit
        unit_properties = await unit.get_all_properties(
            SystemdDBusConstants.UNIT_INTERFACE
        )

        # Extract unit name from object path (proper D-Bus object path parsing)
        object_path = unit.object_path
        unit_name = object_path.split('/')[-1]\
            .replace('_2e', '.')\
            .replace('_2d', '-')

        # Extract job information
        # Job property is a tuple: (job_id, job_type, job_object_path)
        job_info = unit_properties.get(UnitPropertyNames.JOB, (0, '', ''))
        job_id = job_info[0] if len(job_info) > 0 else 0
        job_type = job_info[1] if len(job_info) > 1 else ''
        job_object_path = job_info[2] if len(job_info) > 2 else ''

        return SystemdUnitInfo(
            name=unit_name,
            description=unit_properties.get(UnitPropertyNames.DESCRIPTION, ''),
            load_state=unit_properties.get(UnitPropertyNames.LOAD_STATE, ''),
            active_state=unit_properties.get(
                UnitPropertyNames.ACTIVE_STATE,
                '',
            ),
            sub_state=unit_properties.get(UnitPropertyNames.SUB_STATE, ''),
            following=unit_properties.get(UnitPropertyNames.FOLLOWING, ''),
            object_path=object_path,
            job_id=job_id,
            job_type=job_type,
            job_object_path=job_object_path,
        )


class DBusSystemdUnitParser(SystemdUnitParser):
    """Parser for systemd unit data from D-Bus responses.
    """

    def parse_unit_list_entry(self, unit_data: list) -> SystemdUnitInfo:
        """Parse a single unit entry from D-Bus list_units response.
        """
        if len(unit_data) != 10:
            raise ValueError(
                f'Expected 10 fields in unit data, got {len(unit_data)}'
            )

        return SystemdUnitInfo(
            name=unit_data[0],
            description=unit_data[1],
            load_state=unit_data[2],
            active_state=unit_data[3],
            sub_state=unit_data[4],
            following=unit_data[5],
            object_path=unit_data[6],
            job_id=unit_data[7],
            job_type=unit_data[8],
            job_object_path=unit_data[9],
        )


class DefaultTimerFactory(TimerFactory):
    """Default implementation of timer creation logic.
    """

    def __init__(self, time_converter, boot_time_provider) -> None:
        """Initialize with time conversion dependencies.
        """
        self._time_converter = time_converter
        self._boot_time_provider = boot_time_provider

    def create_timer(
        self,
        unit_info: SystemdUnitInfo,
        properties: TimerProperties,
    ) -> Timer:
        """Create a Timer instance from unit info and properties.
        """
        next_elapse = self._calculate_next_elapse(properties)

        return Timer(
            name=unit_info.name,
            active_state=unit_info.active_state,
            next_elapse=next_elapse,
        )

    def _calculate_next_elapse(
        self,
        properties: TimerProperties,
    ) -> datetime | None:
        """Calculate next elapse time from timer properties.
        """
        if properties.next_elapse_realtime_usec > 0:
            return self._time_converter.convert_realtime_to_datetime(
                properties.next_elapse_realtime_usec
            )

        if properties.next_elapse_monotonic_usec > 0:
            boot_info = self._boot_time_provider.get_boot_time()
            return self._time_converter.convert_monotonic_to_datetime(
                properties.next_elapse_monotonic_usec, boot_info
            )

        return None
