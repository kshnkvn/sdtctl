import logging

from dbus_next.errors import DBusError

from sdtctl.dbus.adapters import (
    DBusSystemdUnitParser,
    DBusTimerPropertiesExtractor,
    DefaultTimerFactory,
)
from sdtctl.dbus.connection import DBusConnectionManager
from sdtctl.dbus.constants import SystemdDBusConstants
from sdtctl.dbus.interfaces import (
    SystemdUnitParser,
    TimerFactory,
    TimerPropertiesExtractor,
)
from sdtctl.models.systemd_unit import TimerProperties
from sdtctl.models.timer import Timer
from sdtctl.system.providers import ProcSystemBootTimeProvider
from sdtctl.time.converters import StandardTimeConverter


class SystemdDBusService:
    """A service for interacting with systemd over D-Bus.
    """

    def __init__(
        self,
        unit_parser: SystemdUnitParser | None = None,
        timer_factory: TimerFactory | None = None,
        properties_extractor: TimerPropertiesExtractor | None = None,
    ) -> None:
        """Initialize the service with optional dependency injection.
        """
        self._logger = logging.getLogger(__name__)

        self._unit_parser = unit_parser or DBusSystemdUnitParser()
        self._timer_factory = timer_factory
        self._properties_extractor = properties_extractor
        self._is_initialized = False
        self._dbus_manager = DBusConnectionManager.get_instance()

    async def _initialize_dependencies(self) -> None:
        """Initialize dependencies that require a D-Bus connection.
        """
        if self._is_initialized:
            return

        bus = await self._dbus_manager.get_bus()

        if not self._properties_extractor:
            self._properties_extractor = DBusTimerPropertiesExtractor(bus)

        if not self._timer_factory:
            time_converter = StandardTimeConverter()
            boot_time_provider = ProcSystemBootTimeProvider()
            self._timer_factory = DefaultTimerFactory(
                time_converter,
                boot_time_provider,
            )

        self._is_initialized = True

    async def list_timers(self) -> list[Timer]:
        """List all timer units.
        """
        await self._initialize_dependencies()

        try:
            raw_units = await self._fetch_raw_units()
            timer_units = self._filter_timer_units(raw_units)

            timers = []
            for unit_data in timer_units:
                timer = await self._process_timer_unit(unit_data)
                if timer:
                    timers.append(timer)

            return timers
        except DBusError as e:
            self._logger.error(
                'Failed to list units due to a D-Bus error: %s',
                e,
                exc_info=True,
            )
            return []
        except Exception as e:
            self._logger.error(
                'An unexpected error occurred while listing timers: %s',
                e,
                exc_info=True,
            )
            return []

    async def _fetch_raw_units(self) -> list:
        """Fetch raw unit data from systemd manager.
        """
        bus = await self._dbus_manager.get_bus()
        introspection = await bus.introspect(
            SystemdDBusConstants.BUS_NAME,
            SystemdDBusConstants.BUS_PATH
        )
        obj = bus.get_proxy_object(
            SystemdDBusConstants.BUS_NAME,
            SystemdDBusConstants.BUS_PATH,
            introspection
        )
        manager = obj.get_interface(SystemdDBusConstants.MANAGER_INTERFACE)
        return await manager.call_list_units()  # type: ignore

    def _filter_timer_units(self, raw_units: list) -> list:
        """Filter units to include only timer units.
        """
        return [
            unit for unit in raw_units
            if unit[0].endswith(SystemdDBusConstants.TIMER_SUFFIX)
        ]

    async def _process_timer_unit(self, unit_data: list) -> Timer | None:
        """Process a single timer unit and return Timer instance.
        """
        try:
            unit_info = self._unit_parser.parse_unit_list_entry(unit_data)
            properties = await self._extract_timer_properties(
                unit_info.object_path
            )
            return self._timer_factory.create_timer(unit_info, properties)  # type: ignore
        except DBusError as e:
            self._logger.warning(
                'D-Bus error while processing timer %s: %s',
                unit_data[0],
                e,
            )
            return None
        except Exception as e:
            self._logger.warning(
                'Failed to process timer %s: %s',
                unit_data[0],
                e,
                exc_info=True,
            )
            return None

    async def _extract_timer_properties(
        self,
        object_path: str,
    ) -> TimerProperties:
        """Extract timer properties with error handling.
        """
        try:
            if not self._properties_extractor:
                # This should not happen if _initialize_dependencies was called
                raise RuntimeError("Properties extractor not initialized.")
            return await self._properties_extractor.extract_timer_properties(  # type: ignore
                object_path
            )
        except DBusError as e:
            self._logger.warning(
                'Failed to extract D-Bus properties for %s: %s',
                object_path,
                e,
            )
        except Exception as e:
            self._logger.warning(
                'An error occurred while extracting properties for %s: %s',
                object_path,
                e,
                exc_info=True
            )
        # Return empty properties as fallback
        return TimerProperties(
            next_elapse_realtime_usec=0,
            next_elapse_monotonic_usec=0,
        )
