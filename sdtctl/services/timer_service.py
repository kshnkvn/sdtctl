from pydantic import ValidationError

from sdtctl.models.creation_results import (
    PermissionResult,
    TimerCreationResult,
    UnitPreview,
)
from sdtctl.models.timer import Timer
from sdtctl.models.timer_config import CreateTimerResult, TimerCreationConfig
from sdtctl.system.unit_file_manager import SystemdDirectoryManager
from sdtctl.systemd import SystemdTimerManager
from sdtctl.systemd.models import TimerCreationRequest


class TimerService:
    """A service for managing systemd timers.
    """

    def __init__(self) -> None:
        """Initialise the service.
        """
        self._manager = SystemdTimerManager()

    async def get_timers(self) -> list[Timer]:
        """Get a list of all systemd timers.
        """
        timer_infos = await self._manager.list_timers()

        # Convert TimerInfo to legacy Timer model for compatibility
        timers = []
        for info in timer_infos:
            timer = Timer(
                name=info.name,
                active_state=info.active_state.value,
                next_elapse=info.next_elapse,
            )
            timers.append(timer)

        return timers

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
            # Convert TimerCreationConfig to TimerCreationRequest
            request = self._convert_config_to_request(config)

            # Create timer using the new adapter
            result = await self._manager.create_timer(request)

            timer_name = self._ensure_timer_suffix(config.name)
            service_name = self._ensure_service_suffix(config.name)

            return CreateTimerResult(
                success=result.success,
                timer_name=timer_name,
                service_name=service_name,
                message=f'Timer {timer_name} created successfully' \
                    if result.success else result.error_message,
                enabled=result.enabled,
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

    def _convert_config_to_request(
        self,
        config: TimerCreationConfig,
    ) -> TimerCreationRequest:
        """Convert legacy TimerCreationConfig to new TimerCreationRequest.
        """
        # Extract timer schedule details
        schedule = config.timer_schedule
        service = config.service_config

        return TimerCreationRequest(
            name=config.name,
            description=config.description,
            command=service.exec_start,
            calendar_spec=schedule.calendar_spec,
            on_boot_sec=schedule.on_boot_sec,
            on_startup_sec=schedule.on_startup_sec,
            on_unit_active_sec=schedule.on_unit_active_sec,
            on_unit_inactive_sec=schedule.on_unit_inactive_sec,
            user=service.user,
            working_directory=service.working_directory,
            environment=service.environment or {},
            persistent=schedule.persistent,
            wake_system=schedule.wake_system,
            accuracy_sec=schedule.accuracy_sec,
            randomized_delay_sec=schedule.randomized_delay_sec,
        )

    async def create_timer_interactive(
        self,
        config: TimerCreationConfig,
        system_level: bool = True,
    ) -> TimerCreationResult:
        """Create a timer from configuration with full validation and setup.
        """
        request = self._convert_config_to_request(config)
        result = await self._manager.create_timer(request, system_level)

        return TimerCreationResult(
            success=result.success,
            timer_name=result.timer_name,
            timer_path=result.timer_path,
            service_path=result.service_path,
            enabled=result.enabled,
            started=False,
            error_message=result.error_message,
        )

    async def preview_timer_creation(
        self,
        config: TimerCreationConfig,
    ) -> UnitPreview:
        """Generate preview of timer units without creating them.
        """
        request = self._convert_config_to_request(config)
        preview = await self._manager.preview_timer(request)

        return UnitPreview(
            timer_content=preview.timer_content,
            service_content=preview.service_content,
            timer_path=preview.timer_path,
            service_path=preview.service_path,
        )

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

    async def start_timer(self, timer_name: str) -> bool:
        """Start a timer.

        Args:
            timer_name: Name of the timer to start (without .timer suffix)

        Returns:
            True if successful, False otherwise
        """
        result = await self._manager.start_timer(timer_name)
        return result.success

    async def stop_timer(self, timer_name: str) -> bool:
        """Stop a timer.

        Args:
            timer_name: Name of the timer to stop (without .timer suffix)

        Returns:
            True if successful, False otherwise
        """
        result = await self._manager.stop_timer(timer_name)
        return result.success

    async def restart_timer(self, timer_name: str) -> bool:
        """Restart a timer.

        Args:
            timer_name: Name of the timer to restart (without .timer suffix)

        Returns:
            True if successful, False otherwise
        """
        result = await self._manager.restart_timer(timer_name)
        return result.success

    async def enable_timer(self, timer_name: str) -> bool:
        """Enable a timer.

        Args:
            timer_name: Name of the timer to enable (without .timer suffix)

        Returns:
            True if successful, False otherwise
        """
        result = await self._manager.enable_timer(timer_name)
        return result.success

    async def disable_timer(self, timer_name: str) -> bool:
        """Disable a timer.

        Args:
            timer_name: Name of the timer to disable (without .timer suffix)

        Returns:
            True if successful, False otherwise
        """
        result = await self._manager.disable_timer(timer_name)
        return result.success

    async def delete_timer(self, timer_name: str, system_level: bool = True) -> bool:
        """Delete a timer.

        Args:
            timer_name: Name of the timer to delete (without .timer suffix)
            system_level: Whether to delete from system level

        Returns:
            True if successful, False otherwise
        """
        result = await self._manager.delete_timer(timer_name, system_level)
        return result.success
