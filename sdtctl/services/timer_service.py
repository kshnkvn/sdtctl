from pydantic import ValidationError

from sdtctl.dbus.systemd import SystemdDBusService
from sdtctl.models.creation_results import (
    PermissionResult,
    TimerCreationResult,
    UnitPreview,
)
from sdtctl.models.timer import Timer
from sdtctl.models.timer_config import CreateTimerResult, TimerCreationConfig
from sdtctl.system.unit_file_manager import SystemdDirectoryManager


class TimerService:
    """A service for managing systemd timers.
    """

    def __init__(self) -> None:
        """Initialise the service.
        """
        self._dbus_service = SystemdDBusService()

    async def get_timers(self) -> list[Timer]:
        """Get a list of all systemd timers.
        """
        return await self._dbus_service.list_timers()

    async def create_timer(
        self,
        config: TimerCreationConfig,
    ) -> CreateTimerResult:
        """Create a new timer.

        Args:
            config: Timer configuration

        Returns:
            CreateTimerResult with success status and details

        Raises:
            ValueError: If configuration validation fails
        """
        try:
            timer_name = self._ensure_timer_suffix(config.name)
            service_name = self._ensure_service_suffix(config.name)

            await self._create_service_unit(
                service_name,
                config.service_config,
            )
            await self._create_timer_unit(timer_name, service_name, config)

            enabled = False
            if config.enabled:
                await self._enable_timer(timer_name)
                enabled = True

            return CreateTimerResult(
                success=True,
                timer_name=timer_name,
                service_name=service_name,
                message=f'Timer {timer_name} created successfully',
                enabled=enabled,
            )

        except Exception as e:
            return CreateTimerResult(
                success=False,
                timer_name=config.name,
                service_name=self._ensure_service_suffix(config.name),
                message=f'Failed to create timer: {str(e)}',
                enabled=False,
            )

    async def validate_timer_config_dict(
        self,
        config_dict: dict,
    ) -> TimerCreationConfig:
        """Validate raw config data and return validated model.

        Args:
            config_dict: Raw configuration dictionary

        Returns:
            Validated TimerCreationConfig instance

        Raises:
            ValueError: If validation fails with detailed error information
        """
        try:
            return TimerCreationConfig(**config_dict)
        except ValidationError as e:
            # Handle validation errors with detailed error info
            raise ValueError(f'Configuration validation failed: {e}')

    def _ensure_timer_suffix(self, name: str) -> str:
        """Ensure timer name has .timer suffix.
        """
        return name if name.endswith('.timer') else f'{name}.timer'

    def _ensure_service_suffix(self, name: str) -> str:
        """Ensure service name has .service suffix.
        """
        base_name = name.removesuffix('.timer')
        return base_name if base_name.endswith('.service')\
            else f'{base_name}.service'

    async def _create_service_unit(
        self,
        service_name: str,
        service_config,
    ) -> None:
        """Create the service unit file.
        """
        # TODO: Implement actual service unit creation
        pass

    async def _create_timer_unit(
        self,
        timer_name: str,
        service_name: str,
        config: TimerCreationConfig,
    ) -> None:
        """Create the timer unit file.
        """
        # TODO: Implement actual timer unit creation
        pass

    async def _enable_timer(self, timer_name: str) -> None:
        """Enable the created timer.
        """
        # TODO: Implement actual timer enabling
        pass

    async def create_timer_interactive(
        self,
        config: TimerCreationConfig,
        system_level: bool = True,
    ) -> TimerCreationResult:
        """Create a timer from configuration with full validation and setup.
        """
        return await self._dbus_service.create_timer(config, system_level)

    async def preview_timer_creation(
        self,
        config: TimerCreationConfig,
    ) -> UnitPreview:
        """Generate preview of timer units without creating them.
        """
        return await self._dbus_service.preview_timer_units(config)

    async def check_creation_permissions(
        self,
        system_level: bool,
    ) -> PermissionResult:
        """Check if current user has permissions to create timers.
        """
        dir_manager = SystemdDirectoryManager()
        target_dir = (
            dir_manager.get_system_unit_dir()
            if system_level
            else dir_manager.get_user_unit_dir()
        )

        return dir_manager.check_directory_permissions(target_dir)
