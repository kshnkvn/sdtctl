from datetime import datetime

from dbus_next.aio.message_bus import MessageBus

from sdtctl.dbus.interfaces import (
    SystemdUnitParser,
    TimerFactory,
    TimerPropertiesExtractor,
)
from sdtctl.dbus.types import DBusVariantValue
from sdtctl.models.systemd_unit import SystemdUnitInfo, TimerProperties
from sdtctl.models.timer import Timer


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


class DBusTimerPropertiesExtractor(TimerPropertiesExtractor):
    """Extracts timer properties from D-Bus systemd objects.
    """

    _BUS_NAME = 'org.freedesktop.systemd1'
    _TIMER_INTERFACE = 'org.freedesktop.systemd1.Timer'
    _PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'

    def __init__(self, bus: MessageBus) -> None:
        """Initialize with D-Bus message bus.
        """
        self._bus = bus

    async def extract_timer_properties(
        self,
        object_path: str,
    ) -> TimerProperties:
        """Extract timer properties from D-Bus object.
        """
        introspection = await self._bus.introspect(self._BUS_NAME, object_path)
        timer_object = self._bus.get_proxy_object(
            self._BUS_NAME,
            object_path,
            introspection,
        )

        timer_object.get_interface(self._TIMER_INTERFACE)
        properties_interface = timer_object.get_interface(
            self._PROPERTIES_INTERFACE
        )
        timer_properties = await properties_interface.call_get_all(  # type: ignore
            self._TIMER_INTERFACE
        )

        realtime_variant = timer_properties.get('NextElapseUSecRealtime')
        monotonic_variant = timer_properties.get('NextElapseUSecMonotonic')

        realtime_usec = DBusVariantValue.from_dbus_variant(
            realtime_variant
        ).value
        monotonic_usec = DBusVariantValue.from_dbus_variant(
            monotonic_variant
        ).value

        return TimerProperties(
            next_elapse_realtime_usec=realtime_usec,
            next_elapse_monotonic_usec=monotonic_usec,
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
