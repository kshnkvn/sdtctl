import logging
from typing import Any

from dbus_next.errors import DBusError

from sdtctl.dbus.connection import DBusConnectionManager
from sdtctl.dbus.constants import SystemdDBusConstants, UnitControlModes
from sdtctl.dbus.unit import SystemdUnit


class SystemdManager:
    """Manages systemd interactions.

    Serves as a factory for SystemdUnit instances
    """

    def __init__(self, dbus_manager: DBusConnectionManager | None = None):
        """Initialize the SystemdManager.

        Args:
            dbus_manager: The D-Bus connection manager.
        """
        self._logger = logging.getLogger(__name__)

        self._dbus_manager = dbus_manager or \
            DBusConnectionManager.get_instance()
        self._manager_proxy = None

    async def _ensure_manager_proxy(self) -> None:
        """Ensure the systemd manager D-Bus proxy is initialized.
        """
        if self._manager_proxy is not None:
            return

        try:
            bus = await self._dbus_manager.get_bus()
            introspection = await bus.introspect(
                SystemdDBusConstants.SERVICE_NAME,
                SystemdDBusConstants.OBJECT_PATH,
            )
            proxy_object = bus.get_proxy_object(
                SystemdDBusConstants.SERVICE_NAME,
                SystemdDBusConstants.OBJECT_PATH,
                introspection,
            )
            self._manager_proxy = proxy_object.get_interface(
                SystemdDBusConstants.MANAGER_INTERFACE
            )
        except DBusError as e:
            self._logger.error(
                'Failed to create systemd manager proxy: %s',
                e,
            )
            raise

    async def list_units(self) -> list[list[Any]]:
        """List all systemd units.

        Returns:
            List of unit data arrays as returned by systemd

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_manager_proxy()

        try:
            return await self._manager_proxy.call_list_units()  # type: ignore
        except DBusError as e:
            self._logger.error(
                'Failed to list systemd units: %s',
                e,
            )
            raise

    async def list_unit_files(self) -> list[list[Any]]:
        """List all systemd unit files.

        Returns:
            List of unit file data arrays as returned by systemd

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_manager_proxy()

        try:
            return await self._manager_proxy.call_list_unit_files()  # type: ignore
        except DBusError as e:
            self._logger.error(
                'Failed to list systemd unit files: %s',
                e,
            )
            raise

    async def get_unit_by_name(self, unit_name: str) -> SystemdUnit:
        """Get a SystemdUnit instance by unit name.

        Args:
            unit_name: The name of the unit (e.g., 'my-timer.timer')

        Returns:
            SystemdUnit instance for the specified unit

        Raises:
            DBusError: If the D-Bus call fails or unit doesn't exist
        """
        await self._ensure_manager_proxy()

        try:
            object_path = await self._manager_proxy.call_get_unit(unit_name)  # type: ignore
            return SystemdUnit(self._dbus_manager, object_path)
        except DBusError as e:
            self._logger.error(
                'Failed to get unit %s: %s',
                unit_name,
                e,
            )
            raise

    async def load_unit(self, unit_name: str) -> SystemdUnit:
        """Load a unit from disk and return a SystemdUnit instance.

        Args:
            unit_name: The name of the unit (e.g., 'my-timer.timer')

        Returns:
            SystemdUnit instance for the loaded unit

        Raises:
            DBusError: If the D-Bus call fails or unit cannot be loaded
        """
        await self._ensure_manager_proxy()

        try:
            object_path = await self._manager_proxy.call_load_unit(unit_name)  # type: ignore
            return SystemdUnit(self._dbus_manager, object_path)
        except DBusError as e:
            self._logger.error(
                'Failed to load unit %s: %s',
                unit_name,
                e,
            )
            raise

    async def start_unit(
        self,
        unit_name: str,
        mode: str = UnitControlModes.REPLACE,
    ) -> str:
        """Start a unit by name.

        Args:
            unit_name: The name of the unit to start
            mode: The start mode (default: 'replace')

        Returns:
            The job object path

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_manager_proxy()

        try:
            job_path = await self._manager_proxy.call_start_unit(  # type: ignore
                unit_name,
                mode,
            )
            return job_path
        except DBusError as e:
            self._logger.error(
                'Failed to start unit %s: %s',
                unit_name,
                e,
            )
            raise

    async def stop_unit(
        self,
        unit_name: str,
        mode: str = UnitControlModes.REPLACE,
    ) -> str:
        """Stop a unit by name.

        Args:
            unit_name: The name of the unit to stop
            mode: The stop mode (default: 'replace')

        Returns:
            The job object path

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_manager_proxy()

        try:
            job_path = await self._manager_proxy.call_stop_unit(  # type: ignore
                unit_name,
                mode,
            )
            return job_path
        except DBusError as e:
            self._logger.error(
                'Failed to stop unit %s: %s',
                unit_name,
                e,
            )
            raise

    async def restart_unit(
        self,
        unit_name: str,
        mode: str = UnitControlModes.REPLACE,
    ) -> str:
        """Restart a unit by name.

        Args:
            unit_name: The name of the unit to restart
            mode: The restart mode (default: 'replace')

        Returns:
            The job object path

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_manager_proxy()

        try:
            job_path = await self._manager_proxy.call_restart_unit(  # type: ignore
                unit_name,
                mode,
            )
            return job_path
        except DBusError as e:
            self._logger.error(
                'Failed to restart unit %s: %s',
                unit_name,
                e,
            )
            raise

    async def enable_unit_files(
        self,
        unit_files: list[str],
        runtime: bool = False,
        force: bool = False,
    ) -> tuple[bool, list[tuple[str, str, str]]]:
        """Enable unit files.

        Args:
            unit_files: List of unit file names to enable
            runtime: Whether to enable for runtime only
            force: Whether to force enable

        Returns:
            Tuple of (carries_install_info, changes)

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_manager_proxy()

        try:
            result = await self._manager_proxy.call_enable_unit_files(  # type: ignore
                unit_files,
                runtime,
                force,
            )
            return result
        except DBusError as e:
            self._logger.error(
                'Failed to enable unit files %s: %s',
                unit_files,
                e,
            )
            raise

    async def disable_unit_files(
        self,
        unit_files: list[str],
        runtime: bool = False,
    ) -> list[tuple[str, str, str]]:
        """Disable unit files.

        Args:
            unit_files: List of unit file names to disable
            runtime: Whether to disable for runtime only

        Returns:
            List of changes

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_manager_proxy()

        try:
            changes = await self._manager_proxy.call_disable_unit_files(  # type: ignore
                unit_files,
                runtime,
            )
            return changes
        except DBusError as e:
            self._logger.error(
                'Failed to disable unit files %s: %s',
                unit_files,
                e,
            )
            raise

    async def reload_daemon(self) -> None:
        """Reload the systemd daemon configuration.

        Raises:
            DBusError: If the D-Bus call fails
        """
        await self._ensure_manager_proxy()

        try:
            await self._manager_proxy.call_reload()  # type: ignore
        except DBusError as e:
            self._logger.error(
                'Failed to reload systemd daemon: %s',
                e,
            )
            raise

    async def get_timer_units(self) -> list[SystemdUnit]:
        """Get all timer units as SystemdUnit instances.

        Returns:
            List of SystemdUnit instances for timer units

        Raises:
            DBusError: If the D-Bus call fails
        """
        units = await self.list_units()
        timer_units = []

        for unit_data in units:
            unit_name = unit_data[0]
            object_path = unit_data[6]

            if unit_name.endswith(SystemdDBusConstants.TIMER_SUFFIX):
                timer_unit = SystemdUnit(self._dbus_manager, object_path)
                timer_units.append(timer_unit)

        return timer_units
