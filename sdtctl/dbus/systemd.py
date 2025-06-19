from typing import NoReturn

from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType

from sdtctl.dbus.adapters import (
    DBusSystemdUnitParser,
    DBusTimerPropertiesExtractor,
    DefaultTimerFactory,
)
from sdtctl.dbus.interfaces import (
    SystemdUnitParser,
    TimerFactory,
    TimerPropertiesExtractor,
)
from sdtctl.models.timer import Timer
from sdtctl.system.providers import ProcSystemBootTimeProvider
from sdtctl.time.converters import StandardTimeConverter


class SystemdDBusService:
    """A service for interacting with systemd over D-Bus.
    """

    _BUS_NAME = 'org.freedesktop.systemd1'
    _BUS_PATH = '/org/freedesktop/systemd1'

    def __init__(
        self,
        unit_parser: SystemdUnitParser | None = None,
        timer_factory: TimerFactory | None = None,
        properties_extractor: TimerPropertiesExtractor | None = None,
    ) -> None:
        """Initialize the service with optional dependency injection.
        """
        self._bus: MessageBus | None = None
        self._unit_parser = unit_parser or DBusSystemdUnitParser()
        self._timer_factory = timer_factory
        self._properties_extractor = properties_extractor

    async def connect(self) -> None:
        """Connect to the system D-Bus.
        """
        self._bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        self._initialize_dependencies()

    def _initialize_dependencies(self) -> None:
        """Initialize dependencies that require D-Bus connection.
        """
        if not self._bus:
            raise RuntimeError('D-Bus connection required')

        if not self._properties_extractor:
            self._properties_extractor = DBusTimerPropertiesExtractor(
                self._bus
            )

        if not self._timer_factory:
            time_converter = StandardTimeConverter()
            boot_time_provider = ProcSystemBootTimeProvider()
            self._timer_factory = DefaultTimerFactory(
                time_converter,
                boot_time_provider,
            )

    async def list_timers(self) -> list[Timer]:
        """List all timer units.
        """
        self._ensure_connected()

        raw_units = await self._fetch_raw_units()
        timer_units = self._filter_timer_units(raw_units)

        timers = []
        for unit_data in timer_units:
            timer = await self._process_timer_unit(unit_data)
            if timer:
                timers.append(timer)

        return timers

    def _ensure_connected(self) -> None:
        """Ensure D-Bus connection is established.
        """
        if not self._bus:
            raise RuntimeError('Not connected to D-Bus.')

    async def _fetch_raw_units(self) -> list:
        """Fetch raw unit data from systemd manager.
        """
        introspection = await self._bus.introspect(  # type: ignore
            self._BUS_NAME,
            self._BUS_PATH,
        )
        obj = self._bus.get_proxy_object(  # type: ignore
            self._BUS_NAME,
            self._BUS_PATH,
            introspection,
        )
        manager = obj.get_interface('org.freedesktop.systemd1.Manager')
        return await manager.call_list_units()  # type: ignore

    def _filter_timer_units(self, raw_units: list) -> list:
        """Filter units to include only timer units.
        """
        return [unit for unit in raw_units if unit[0].endswith('.timer')]

    async def _process_timer_unit(self, unit_data: list) -> Timer | None:
        """Process a single timer unit and return Timer instance.
        """
        try:
            unit_info = self._unit_parser.parse_unit_list_entry(unit_data)
            properties = await self._extract_timer_properties(
                unit_info.object_path
            )
            return self._timer_factory.create_timer(unit_info, properties)  # type: ignore
        except Exception as e:
            print(f'Warning: Failed to process timer {unit_data[0]}: {e}')
            return None

    async def _extract_timer_properties(self, object_path: str):
        """Extract timer properties with error handling.
        """
        try:
            return await self._properties_extractor.extract_timer_properties(  # type: ignore
                object_path
            )
        except Exception as e:
            print(
                f'Warning: Failed to extract properties for '
                f'{object_path}: {e}'
            )
            # Return empty properties as fallback
            from sdtctl.models.systemd_unit import TimerProperties
            return TimerProperties(
                next_elapse_realtime_usec=0,
                next_elapse_monotonic_usec=0,
            )

    def _assert_never(self, value: NoReturn) -> NoReturn:
        raise AssertionError(f'Unhandled value: {value}')
