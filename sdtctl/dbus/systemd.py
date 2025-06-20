import logging

from dbus_next.errors import DBusError
from pydantic import ValidationError

from sdtctl.dbus.adapters import (
    DBusSystemdUnitParser,
    DefaultTimerFactory,
    SystemdUnitInfoFactory,
)
from sdtctl.dbus.connection import DBusConnectionManager
from sdtctl.dbus.constants import TimerPropertyNames
from sdtctl.dbus.interfaces import (
    SystemdUnitParser,
    TimerFactory,
)
from sdtctl.dbus.manager import SystemdManager
from sdtctl.dbus.unit import SystemdUnit
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
        systemd_manager: SystemdManager | None = None,
    ) -> None:
        """Initialize the service with optional dependency injection.

        Args:
            unit_parser: Parser for systemd unit data
            timer_factory: Factory for creating Timer instances
            systemd_manager: SystemdManager instance for D-Bus operations
        """
        self._logger = logging.getLogger(__name__)

        self._unit_parser = unit_parser or DBusSystemdUnitParser()
        self._timer_factory = timer_factory
        self._systemd_manager = systemd_manager
        self._is_initialized = False

    async def _initialize_dependencies(self) -> None:
        """Initialize dependencies that require setup.
        """
        if self._is_initialized:
            return

        if not self._systemd_manager:
            dbus_manager = DBusConnectionManager.get_instance()
            self._systemd_manager = SystemdManager(dbus_manager)

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

        Returns:
            List of Timer instances
        """
        await self._initialize_dependencies()

        try:
            timer_units = await self._systemd_manager.get_timer_units()  # type: ignore
            timers = []

            for unit in timer_units:
                timer = await self._process_timer_unit(unit)
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

    async def _process_timer_unit(self, unit: SystemdUnit) -> Timer | None:
        """Process a SystemdUnit and return Timer instance.

        Args:
            unit: SystemdUnit instance to process

        Returns:
            Timer instance or None if processing fails
        """
        try:
            # Create SystemdUnitInfo directly from the SystemdUnit
            unit_info = await SystemdUnitInfoFactory\
                .create_from_systemd_unit(unit)

            # Extract timer properties
            timer_properties = await self._extract_timer_properties(unit)

            # Create Timer using the factory
            return self._timer_factory.create_timer( # type: ignore
                unit_info,
                timer_properties,
            )

        except DBusError as e:
            self._logger.warning(
                'D-Bus error while processing timer %s: %s',
                unit.object_path,
                e,
            )
            return None
        except Exception as e:
            self._logger.warning(
                'Failed to process timer %s: %s',
                unit.object_path,
                e,
                exc_info=True,
            )
            return None

    async def _extract_timer_properties(
        self,
        unit: SystemdUnit,
    ) -> TimerProperties:
        """Extract timer properties from a SystemdUnit.

        Args:
            unit: SystemdUnit instance to extract properties from

        Returns:
            TimerProperties instance
        """
        try:
            timer_properties = await unit.get_timer_properties()

            realtime_usec = timer_properties.get(
                TimerPropertyNames.NEXT_ELAPSE_REALTIME_USEC,
                0,
            )
            monotonic_usec = timer_properties.get(
                TimerPropertyNames.NEXT_ELAPSE_MONOTONIC_USEC,
                0,
            )

            # Extract optional properties if available
            last_trigger = timer_properties.get(
                TimerPropertyNames.LAST_TRIGGER_USEC,
                None,
            )
            result = timer_properties.get(
                TimerPropertyNames.RESULT,
                None,
            )

            try:
                return TimerProperties(
                    next_elapse_realtime_usec=realtime_usec,
                    next_elapse_monotonic_usec=monotonic_usec,
                    last_trigger_usec=last_trigger,
                    result=result,
                )
            except ValidationError as e:
                self._logger.warning(
                    'Invalid timer properties for %s: %s',
                    unit.object_path,
                    e,
                )
                # Return fallback with zero values
                return TimerProperties(
                    next_elapse_realtime_usec=0,
                    next_elapse_monotonic_usec=0,
                    last_trigger_usec=None,
                    result=None,
                )
        except DBusError as e:
            self._logger.warning(
                'Failed to extract D-Bus properties for %s: %s',
                unit.object_path,
                e,
            )
        except Exception as e:
            self._logger.warning(
                'An error occurred while extracting properties for %s: %s',
                unit.object_path,
                e,
                exc_info=True,
            )
        # Return empty properties as fallback
        try:
            return TimerProperties(
                next_elapse_realtime_usec=0,
                next_elapse_monotonic_usec=0,
                last_trigger_usec=None,
                result=None,
            )
        except ValidationError as e:
            self._logger.error(
                'Failed to create fallback timer properties: %s',
                e,
            )
            raise
