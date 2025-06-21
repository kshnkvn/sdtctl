import logging
from datetime import datetime
from typing import Any

from dbus_next.errors import DBusError

from sdtctl.system.unit_file_manager import UnitFileManager
from sdtctl.systemd.connection import DBusConnectionManager
from sdtctl.systemd.models import (
    DBusTimerProperties,
    DBusUnitData,
    DBusVariantValue,
    TimerCreationRequest,
    TimerCreationResult,
    TimerInfo,
    TimerOperationResult,
    TimerPreview,
)
from sdtctl.systemd.types import (
    DBusConstants,
    SystemdDBusConstants,
    TimerOperation,
    TimerPropertyNames,
    UnitActiveState,
    UnitControlModes,
    UnitFileState,
    UnitLoadState,
)
from sdtctl.time.converters import StandardTimeConverter


class SystemdTimerManager:
    """Unified manager for all systemd timer operations via D-Bus.

    This is the main interface for interacting with systemd timers.
    """

    def __init__(self) -> None:
        """Initialize the manager with required dependencies."""
        self._logger = logging.getLogger(__name__)
        self._connection = DBusConnectionManager.get_instance()
        self._file_manager = UnitFileManager()
        self._time_converter = StandardTimeConverter()
        self._manager_proxy = None

    async def list_timers(self) -> list[TimerInfo]:
        """List all systemd timers with their information.

        Returns:
            List of TimerInfo objects containing timer details
        """
        try:
            await self._ensure_manager_proxy()
            units_data = await self._manager_proxy.call_list_units()  # type: ignore

            timers = []
            for unit_data in units_data:
                if self._is_timer_unit(unit_data[0]):
                    timer_info = await self._build_timer_info(unit_data)
                    if timer_info:
                        timers.append(timer_info)

            return timers

        except DBusError as e:
            self._logger.error(f'Failed to list timers: {e}')
            return []
        except Exception as e:
            self._logger.error(f'Unexpected error listing timers: {e}')
            return []

    async def create_timer(
        self,
        request: TimerCreationRequest,
        system_level: bool = True,
    ) -> TimerCreationResult:
        """Create and install a new timer.

        Args:
            request: Timer creation configuration
            system_level: Whether to install at system level

        Returns:
            TimerCreationResult with creation details
        """
        try:
            # Generate unit file contents
            timer_content = self._generate_timer_unit(request)
            service_content = self._generate_service_unit(request)

            # Write unit files
            timer_path = await self._file_manager.write_unit_file(
                f'{request.name}.timer',
                timer_content,
                system_level,
            )
            service_path = await self._file_manager.write_unit_file(
                f'{request.name}.service',
                service_content,
                system_level,
            )

            # Reload systemd and enable timer
            await self._reload_daemon()
            enabled = await self._enable_timer(request.name)

            return TimerCreationResult(
                success=True,
                timer_name=request.name,
                timer_path=timer_path,
                service_path=service_path,
                enabled=enabled,
                error_message='',
            )

        except Exception as e:
            self._logger.error(f'Failed to create timer {request.name}: {e}')
            return TimerCreationResult(
                success=False,
                timer_name=request.name,
                timer_path=None,
                service_path=None,
                enabled=False,
                error_message=str(e),
            )

    async def delete_timer(
        self,
        timer_name: str,
        system_level: bool = True,
    ) -> TimerOperationResult:
        """Delete a timer and its associated service unit.

        Args:
            timer_name: Name of the timer to delete
            system_level: Whether to delete from system level

        Returns:
            TimerOperationResult with operation details
        """
        try:
            # Stop and disable first
            await self._stop_timer(timer_name)
            await self._disable_timer(timer_name)

            # Remove unit files
            timer_file = f'{timer_name}.timer'
            service_file = f'{timer_name}.service'

            await self._file_manager.remove_unit_file(timer_file, system_level)
            await self._file_manager.remove_unit_file(
                service_file,
                system_level,
            )

            # Reload daemon
            await self._reload_daemon()

            return TimerOperationResult(
                success=True,
                timer_name=timer_name,
                operation=TimerOperation.DELETE,
                message=f'Timer {timer_name} deleted successfully',
                job_path='',
            )

        except Exception as e:
            self._logger.error(f'Failed to delete timer {timer_name}: {e}')
            return TimerOperationResult(
                success=False,
                timer_name=timer_name,
                operation=TimerOperation.DELETE,
                message=str(e),
                job_path='',
            )

    async def start_timer(self, timer_name: str) -> TimerOperationResult:
        """Start a timer.

        Args:
            timer_name: Name of the timer to start

        Returns:
            TimerOperationResult with operation details
        """
        return await self._control_timer(timer_name, TimerOperation.START)

    async def stop_timer(self, timer_name: str) -> TimerOperationResult:
        """Stop a timer.

        Args:
            timer_name: Name of the timer to stop

        Returns:
            TimerOperationResult with operation details
        """
        return await self._control_timer(timer_name, TimerOperation.STOP)

    async def restart_timer(self, timer_name: str) -> TimerOperationResult:
        """Restart a timer.

        Args:
            timer_name: Name of the timer to restart

        Returns:
            TimerOperationResult with operation details
        """
        return await self._control_timer(timer_name, TimerOperation.RESTART)

    async def enable_timer(self, timer_name: str) -> TimerOperationResult:
        """Enable a timer.

        Args:
            timer_name: Name of the timer to enable

        Returns:
            TimerOperationResult with operation details
        """
        try:
            enabled = await self._enable_timer(timer_name)
            return TimerOperationResult(
                success=enabled,
                timer_name=timer_name,
                operation=TimerOperation.ENABLE,
                message=f'Timer {timer_name} enabled' \
                    if enabled else 'Failed to enable timer',
                job_path='',
            )
        except Exception as e:
            self._logger.error(f'Failed to enable timer {timer_name}: {e}')
            return TimerOperationResult(
                success=False,
                timer_name=timer_name,
                operation=TimerOperation.ENABLE,
                message=str(e),
                job_path='',
            )

    async def disable_timer(self, timer_name: str) -> TimerOperationResult:
        """Disable a timer.

        Args:
            timer_name: Name of the timer to disable

        Returns:
            TimerOperationResult with operation details
        """
        try:
            disabled = await self._disable_timer(timer_name)
            return TimerOperationResult(
                success=disabled,
                timer_name=timer_name,
                operation=TimerOperation.DISABLE,
                message=f'Timer {timer_name} disabled' \
                    if disabled else 'Failed to disable timer',
                job_path='',
            )
        except Exception as e:
            self._logger.error(f'Failed to disable timer {timer_name}: {e}')
            return TimerOperationResult(
                success=False,
                timer_name=timer_name,
                operation=TimerOperation.DISABLE,
                message=str(e),
                job_path='',
            )

    async def preview_timer(
        self,
        request: TimerCreationRequest,
    ) -> TimerPreview:
        """Preview timer unit files without creating them.

        Args:
            request: Timer creation configuration

        Returns:
            TimerPreview with unit file contents and paths
        """
        timer_content = self._generate_timer_unit(request)
        service_content = self._generate_service_unit(request)

        timer_path = await self._file_manager.get_unit_file_path(
            f'{request.name}.timer',
            system_level=True,
        )
        service_path = await self._file_manager.get_unit_file_path(
            f'{request.name}.service',
            system_level=True,
        )

        return TimerPreview(
            timer_content=timer_content,
            service_content=service_content,
            timer_path=timer_path,
            service_path=service_path,
        )

    async def _ensure_manager_proxy(self) -> None:
        """Ensure the systemd manager proxy is initialized.
        """
        if self._manager_proxy is not None:
            return

        bus = await self._connection.get_bus()
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

    def _is_timer_unit(self, unit_name: str) -> bool:
        """Check if a unit name represents a timer.
        """
        return unit_name.endswith(SystemdDBusConstants.TIMER_SUFFIX)

    async def _build_timer_info(
        self,
        unit_data: list[Any],
    ) -> TimerInfo | None:
        """Build TimerInfo from raw unit data.
        """
        try:
            dbus_data = DBusUnitData(
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

            # Get timer properties and file state
            timer_props = await self._get_timer_properties(
                dbus_data.object_path,
            )
            file_state = await self._get_unit_file_state(dbus_data.name)

            # Convert timestamps
            next_elapse = self._convert_next_elapse(timer_props)
            last_trigger = self._convert_last_trigger(timer_props)

            return TimerInfo(
                name=dbus_data.name,
                description=dbus_data.description,
                active_state=UnitActiveState(dbus_data.active_state),
                load_state=UnitLoadState(dbus_data.load_state),
                file_state=UnitFileState(file_state),
                next_elapse=next_elapse,
                last_trigger=last_trigger,
                object_path=dbus_data.object_path,
            )

        except Exception as e:
            self._logger.warning(
                f'Failed to build timer info for {unit_data[0]}: {e}'
            )
            return None

    async def _get_timer_properties(
        self,
        object_path: str,
    ) -> DBusTimerProperties:
        """Get timer properties from D-Bus.
        """
        bus = await self._connection.get_bus()
        introspection = await bus.introspect(
            SystemdDBusConstants.SERVICE_NAME,
            object_path,
        )
        proxy_object = bus.get_proxy_object(
            SystemdDBusConstants.SERVICE_NAME,
            object_path,
            introspection,
        )
        properties_interface = proxy_object.get_interface(
            DBusConstants.PROPERTIES_INTERFACE
        )

        raw_props = await properties_interface.call_get_all( # type: ignore
            SystemdDBusConstants.TIMER_INTERFACE
        )

        # Convert variants to Python values
        props = {}
        for name, variant in raw_props.items():
            props[name] = DBusVariantValue.from_dbus_variant(variant).value

        return DBusTimerProperties(
            next_elapse_realtime_usec=props.get(
                TimerPropertyNames.NEXT_ELAPSE_REALTIME_USEC,
                0,
            ),
            next_elapse_monotonic_usec=props.get(
                TimerPropertyNames.NEXT_ELAPSE_MONOTONIC_USEC,
                0,
            ),
            last_trigger_usec=props.get(TimerPropertyNames.LAST_TRIGGER_USEC),
            result=props.get(TimerPropertyNames.RESULT),
            accuracy_usec=props.get(
                TimerPropertyNames.ACCURACY_USEC,
                60000000,
            ),
            randomized_delay_usec=props.get(
                TimerPropertyNames.RANDOMIZED_DELAY_USEC,
                0,
            ),
            persistent=props.get(TimerPropertyNames.PERSISTENT, False),
            wake_system=props.get(TimerPropertyNames.WAKE_SYSTEM, False),
            remain_after_elapse=props.get(
                TimerPropertyNames.REMAIN_AFTER_ELAPSE,
                True,
            ),
        )

    async def _get_unit_file_state(self, unit_name: str) -> str:
        """Get unit file state.
        """
        await self._ensure_manager_proxy()
        try:
            return await self._manager_proxy.call_get_unit_file_state( # type: ignore
                unit_name
            )
        except DBusError:
            return UnitFileState.DISABLED.value

    def _convert_next_elapse(
        self,
        props: DBusTimerProperties,
    ) -> datetime | None:
        """Convert next elapse time to datetime.
        """
        if props.next_elapse_realtime_usec > 0:
            return self._time_converter.convert_realtime_to_datetime(
                props.next_elapse_realtime_usec
            )
        return None

    def _convert_last_trigger(
        self,
        props: DBusTimerProperties,
    ) -> datetime | None:
        """Convert last trigger time to datetime.
        """
        if props.last_trigger_usec and props.last_trigger_usec > 0:
            return self._time_converter.convert_realtime_to_datetime(
                props.last_trigger_usec
            )
        return None

    async def _control_timer(
        self,
        timer_name: str,
        operation: TimerOperation,
    ) -> TimerOperationResult:
        """Generic timer control operation.
        """
        try:
            await self._ensure_manager_proxy()
            unit_name = f'{timer_name}.timer'

            if operation == TimerOperation.START:
                job_path = await self._manager_proxy.call_start_unit(  # type: ignore
                    unit_name, UnitControlModes.REPLACE
                )
            elif operation == TimerOperation.STOP:
                job_path = await self._manager_proxy.call_stop_unit(  # type: ignore
                    unit_name, UnitControlModes.REPLACE
                )
            elif operation == TimerOperation.RESTART:
                job_path = await self._manager_proxy.call_restart_unit(  # type: ignore
                    unit_name, UnitControlModes.REPLACE
                )
            else:
                raise ValueError(f'Unsupported operation: {operation}')

            return TimerOperationResult(
                success=True,
                timer_name=timer_name,
                operation=operation,
                message=f'Timer {timer_name} {operation.value}ed successfully',
                job_path=job_path,
            )

        except Exception as e:
            self._logger.error(
                f'Failed to {operation.value} timer {timer_name}: {e}'
            )
            return TimerOperationResult(
                success=False,
                timer_name=timer_name,
                operation=operation,
                message=str(e),
                job_path='',
            )

    async def _stop_timer(self, timer_name: str) -> None:
        """Stop timer (internal helper).
        """
        await self._ensure_manager_proxy()
        unit_name = f'{timer_name}.timer'
        try:
            await self._manager_proxy.call_stop_unit(  # type: ignore
                unit_name, UnitControlModes.REPLACE
            )
        except DBusError:
            pass  # Ignore if already stopped

    async def _enable_timer(self, timer_name: str) -> bool:
        """Enable timer (internal helper).
        """
        await self._ensure_manager_proxy()
        unit_file = f'{timer_name}.timer'
        try:
            result = await self._manager_proxy.call_enable_unit_files(  # type: ignore
                [unit_file], False, True
            )
            await self._reload_daemon()
            return result[0]  # carries_install_info
        except DBusError as e:
            self._logger.error(f'Failed to enable timer {timer_name}: {e}')
            return False

    async def _disable_timer(self, timer_name: str) -> bool:
        """Disable timer (internal helper).
        """
        await self._ensure_manager_proxy()
        unit_file = f'{timer_name}.timer'
        try:
            await self._manager_proxy.call_disable_unit_files(  # type: ignore
                [unit_file], False
            )
            await self._reload_daemon()
            return True
        except DBusError as e:
            self._logger.error(f'Failed to disable timer {timer_name}: {e}')
            return False

    async def _reload_daemon(self) -> None:
        """Reload systemd daemon.
        """
        await self._ensure_manager_proxy()
        await self._manager_proxy.call_reload()  # type: ignore

    def _generate_timer_unit(self, request: TimerCreationRequest) -> str:
        """Generate timer unit file content.
        """
        lines = [
            '[Unit]',
            f'Description={request.description}',
            f'Documentation=Timer for {request.name}',
            '',
            '[Timer]',
        ]

        # Add timer specifications
        if request.calendar_spec:
            lines.append(f'OnCalendar={request.calendar_spec}')
        if request.on_boot_sec is not None:
            lines.append(f'OnBootSec={request.on_boot_sec}')
        if request.on_startup_sec is not None:
            lines.append(f'OnStartupSec={request.on_startup_sec}')
        if request.on_unit_active_sec is not None:
            lines.append(f'OnUnitActiveSec={request.on_unit_active_sec}')
        if request.on_unit_inactive_sec is not None:
            lines.append(f'OnUnitInactiveSec={request.on_unit_inactive_sec}')

        # Timer behavior options
        if request.accuracy_sec != 60:
            lines.append(f'AccuracySec={request.accuracy_sec}')
        if request.randomized_delay_sec > 0:
            lines.append(f'RandomizedDelaySec={request.randomized_delay_sec}')
        if request.persistent:
            lines.append('Persistent=true')
        if request.wake_system:
            lines.append('WakeSystem=true')

        lines.extend(['', '[Install]', 'WantedBy=timers.target', ''])

        return '\n'.join(lines)

    def _generate_service_unit(self, request: TimerCreationRequest) -> str:
        """Generate service unit file content.
        """
        lines = [
            '[Unit]',
            f'Description=Service for {request.description}',
            f'Documentation=Service unit for {request.name} timer',
            '',
            '[Service]',
            'Type=oneshot',
            f'ExecStart={request.command}',
        ]

        if request.user:
            lines.append(f'User={request.user}')
        if request.working_directory:
            lines.append(f'WorkingDirectory={request.working_directory}')

        for key, value in request.environment.items():
            lines.append(f'Environment="{key}={value}"')

        lines.append('')

        return '\n'.join(lines)
