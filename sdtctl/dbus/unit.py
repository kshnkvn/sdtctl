import logging
from typing import Any

from dbus_next.errors import DBusError

from sdtctl.dbus.connection import DBusConnectionManager
from sdtctl.dbus.constants import (
    DBusConstants,
    SystemdDBusConstants,
    UnitControlModes,
    UnitPropertyNames,
)
from sdtctl.dbus.types import DBusVariantValue


class SystemdUnit:
    """Represents a systemd unit.

    Provides methods to interact with it via D-Bus.
    """

    def __init__(self, dbus_manager: DBusConnectionManager, object_path: str):
        """Initialize a SystemdUnit instance.

        Args:
            dbus_manager: The D-Bus connection manager
            object_path: The D-Bus object path for this unit
        """
        self._logger = logging.getLogger(__name__)

        self._dbus_manager = dbus_manager
        self._object_path = object_path
        self._proxy_object = None

    @property
    def object_path(self) -> str:
        """Get the D-Bus object path for this unit.

        Returns:
            The object path string
        """
        return self._object_path

    async def _ensure_proxy(self) -> None:
        """Ensure the D-Bus proxy object is initialized.
        """
        if self._proxy_object is not None:
            return

        try:
            bus = await self._dbus_manager.get_bus()
            introspection = await bus.introspect(
                SystemdDBusConstants.SERVICE_NAME,
                self._object_path,
            )
            self._proxy_object = bus.get_proxy_object(
                SystemdDBusConstants.SERVICE_NAME,
                self._object_path,
                introspection,
            )
        except DBusError as e:
            self._logger.error(
                'Failed to create proxy for unit %s: %s',
                self._object_path,
                e,
            )
            raise

    async def get_property(self, interface: str, property_name: str) -> Any:
        """Get a single property from the unit.

        Args:
            interface: The D-Bus interface name
            property_name: The property name to retrieve

        Returns:
            The property value

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_proxy()

        try:
            properties_interface = self._proxy_object.get_interface( # type: ignore
                DBusConstants.PROPERTIES_INTERFACE
            )
            variant = await properties_interface.call_get( # type: ignore
                interface,
                property_name,
            )
            return DBusVariantValue.from_dbus_variant(variant).value
        except DBusError as e:
            self._logger.warning(
                'Failed to get property %s.%s for unit %s: %s',
                interface,
                property_name,
                self._object_path,
                e,
            )
            raise

    async def get_all_properties(self, interface: str) -> dict[str, Any]:
        """Get all properties from a specific interface.

        Args:
            interface: The D-Bus interface name

        Returns:
            Dictionary of property names to values

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_proxy()

        try:
            properties_interface = self._proxy_object.get_interface( # type: ignore
                DBusConstants.PROPERTIES_INTERFACE
            )
            raw_properties = await properties_interface.call_get_all( # type: ignore
                interface
            )

            # Convert all variant values to Python values
            properties = {}
            for name, variant in raw_properties.items():
                properties[name] = DBusVariantValue\
                    .from_dbus_variant(variant).value

            return properties
        except DBusError as e:
            self._logger.warning(
                'Failed to get all properties for interface %s on unit %s: %s',
                interface,
                self._object_path,
                e,
            )
            raise

    async def get_active_state(self) -> str:
        """Get the active state of the unit.

        Returns:
            The active state string (e.g., 'active', 'inactive', 'failed')

        Raises:
            DBusError: If the D-Bus call fails
        """
        return await self.get_property(
            SystemdDBusConstants.UNIT_INTERFACE,
            UnitPropertyNames.ACTIVE_STATE,
        )

    async def get_load_state(self) -> str:
        """Get the load state of the unit.

        Returns:
            The load state string (e.g., 'loaded', 'not-found', 'error')

        Raises:
            DBusError: If the D-Bus call fails
        """
        return await self.get_property(
            SystemdDBusConstants.UNIT_INTERFACE,
            UnitPropertyNames.LOAD_STATE,
        )

    async def get_sub_state(self) -> str:
        """Get the sub state of the unit.

        Returns:
            The sub state string

        Raises:
            DBusError: If the D-Bus call fails
        """
        return await self.get_property(
            SystemdDBusConstants.UNIT_INTERFACE,
            UnitPropertyNames.SUB_STATE,
        )

    async def start(self, mode: str = UnitControlModes.REPLACE) -> str:
        """Start the unit.

        Args:
            mode: The start mode (default: 'replace')

        Returns:
            The job object path

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_proxy()

        try:
            unit_interface = self._proxy_object.get_interface( # type: ignore
                SystemdDBusConstants.UNIT_INTERFACE
            )
            job_path = await unit_interface.call_start(mode) # type: ignore
            return job_path
        except DBusError as e:
            self._logger.error(
                'Failed to start unit %s: %s',
                self._object_path,
                e,
            )
            raise

    async def stop(self, mode: str = UnitControlModes.REPLACE) -> str:
        """Stop the unit.

        Args:
            mode: The stop mode (default: 'replace')

        Returns:
            The job object path

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_proxy()

        try:
            unit_interface = self._proxy_object.get_interface( # type: ignore
                SystemdDBusConstants.UNIT_INTERFACE
            )
            job_path = await unit_interface.call_stop(mode)  # type: ignore
            return job_path
        except DBusError as e:
            self._logger.error(
                'Failed to stop unit %s: %s',
                self._object_path,
                e,
            )
            raise

    async def restart(self, mode: str = UnitControlModes.REPLACE) -> str:
        """Restart the unit.

        Args:
            mode: The restart mode (default: 'replace')

        Returns:
            The job object path

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_proxy()

        try:
            unit_interface = self._proxy_object.get_interface( # type: ignore
                SystemdDBusConstants.UNIT_INTERFACE
            )
            job_path = await unit_interface.call_restart(mode) # type: ignore
            return job_path
        except DBusError as e:
            self._logger.error(
                'Failed to restart unit %s: %s',
                self._object_path,
                e,
            )
            raise

    async def get_timer_properties(self) -> dict[str, Any]:
        """Get timer-specific properties (for timer units only).

        Returns:
            Dictionary of timer properties

        Raises:
            DBusError: If the D-Bus call fails or unit is not a timer
        """
        return await self.get_all_properties(
            SystemdDBusConstants.TIMER_INTERFACE
        )
