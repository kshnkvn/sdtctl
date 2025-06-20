import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

from sdtctl.models.creation_results import (
    PermissionResult,
    UnitFileWriteResult,
)
from sdtctl.models.timer_config import TimerCreationConfig
from sdtctl.system.constants import SystemdPaths


class SystemdDirectoryManager:
    """Manages systemd configuration directories.
    """

    def __init__(self) -> None:
        """Initialize the directory manager.
        """
        self._logger = logging.getLogger(__name__)

    def get_system_unit_dir(self) -> Path:
        """Get system-level unit directory path.
        """
        return Path(SystemdPaths.SYSTEM_UNIT_DIR)

    def get_user_unit_dir(self) -> Path:
        """Get user-level unit directory path.
        """
        home_dir = Path.home()
        return home_dir / SystemdPaths.USER_CONFIG_DIR

    def ensure_directory_exists(self, path: Path) -> None:
        """Ensure directory exists, create if necessary.
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
            self._logger.debug('Ensured directory exists: %s', path)
        except Exception as e:
            self._logger.error(
                'Failed to create directory %s: %s',
                path,
                e,
                exc_info=True,
            )
            raise

    def check_directory_permissions(self, path: Path) -> PermissionResult:
        """Check directory permissions for read/write access.
        """
        try:
            if not path.exists():
                return PermissionResult(
                    has_permission=False,
                    required_permission='read/write',
                    error_message=f'Directory does not exist: {path}',
                )

            if not os.access(path, os.R_OK | os.W_OK):
                return PermissionResult(
                    has_permission=False,
                    required_permission='read/write',
                    error_message=f'No read/write permission: {path}',
                )

            return PermissionResult(
                has_permission=True,
                required_permission='read/write',
            )

        except Exception as e:
            return PermissionResult(
                has_permission=False,
                required_permission='read/write',
                error_message=f'Permission check failed: {e}',
            )

    def get_backup_directory(self, system_level: bool) -> Path:
        """Get directory for backing up existing unit files.
        """
        if system_level:
            return Path(SystemdPaths.SYSTEM_BACKUP_DIR)
        else:
            home_dir = Path.home()
            return home_dir / SystemdPaths.USER_BACKUP_DIR


class UnitFileManager:
    """Manages systemd unit file operations on the filesystem.
    """

    def __init__(
        self,
        directory_manager: SystemdDirectoryManager | None = None,
    ) -> None:
        """Initialize with optional directory manager.
        """
        self._logger = logging.getLogger(__name__)

        self._dir_manager = directory_manager or SystemdDirectoryManager()

    async def write_timer_files(
        self,
        config: TimerCreationConfig,
        timer_content: str,
        service_content: str,
        system_level: bool = True,
    ) -> UnitFileWriteResult:
        """Write timer and service unit files to appropriate directory.
        """
        try:
            timer_name = self._ensure_suffix(config.name, '.timer')
            service_name = self._ensure_suffix(
                config.name.removesuffix('.timer'),
                '.service',
            )

            timer_path = await self.get_unit_file_path(
                timer_name,
                system_level,
            )
            service_path = await self.get_unit_file_path(
                service_name,
                system_level,
            )

            target_dir = timer_path.parent
            permission_result = \
                await self.validate_write_permissions(target_dir)
            if not permission_result.has_permission:
                return UnitFileWriteResult(
                    success=False,
                    error_message=permission_result.error_message,
                )

            # Backup existing files if they exist
            backup_paths = []
            if await self.check_unit_file_exists(timer_name, system_level):
                backup_path = await self.backup_existing_unit(timer_path)
                backup_paths.append(backup_path)

            if await self.check_unit_file_exists(service_name, system_level):
                backup_path = await self.backup_existing_unit(service_path)
                backup_paths.append(backup_path)

            # Ensure target directory exists
            self._dir_manager.ensure_directory_exists(target_dir)

            # Write files atomically (write to temp files first)
            timer_temp = timer_path.with_suffix('.timer.tmp')
            service_temp = service_path.with_suffix('.service.tmp')

            try:
                # Write timer file
                timer_temp.write_text(timer_content, encoding='utf-8')

                # Write service file
                service_temp.write_text(service_content, encoding='utf-8')

                # Atomic move
                timer_temp.rename(timer_path)
                service_temp.rename(service_path)

                # Set appropriate permissions
                timer_path.chmod(0o644)
                service_path.chmod(0o644)

                return UnitFileWriteResult(
                    success=True,
                    timer_path=timer_path,
                    service_path=service_path,
                    backup_paths=backup_paths if backup_paths else None,
                )

            except Exception as e:
                # Clean up temp files on error
                for temp_file in [timer_temp, service_temp]:
                    if temp_file.exists():
                        temp_file.unlink()
                raise e

        except Exception as e:
            self._logger.error(
                'Failed to write timer files for %s: %s',
                config.name,
                e,
                exc_info=True,
            )
            return UnitFileWriteResult(
                success=False,
                error_message=str(e),
            )

    async def get_unit_file_path(
        self,
        unit_name: str,
        system_level: bool,
    ) -> Path:
        """Get the full path for a unit file.
        """
        if system_level:
            base_dir = self._dir_manager.get_system_unit_dir()
        else:
            base_dir = self._dir_manager.get_user_unit_dir()

        return base_dir / unit_name

    async def check_unit_file_exists(
        self,
        unit_name: str,
        system_level: bool,
    ) -> bool:
        """Check if unit file already exists.
        """
        unit_path = await self.get_unit_file_path(unit_name, system_level)
        return unit_path.exists()

    async def backup_existing_unit(self, unit_path: Path) -> Path:
        """Create backup of existing unit file.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = unit_path.with_suffix(
            f'{unit_path.suffix}.bak.{timestamp}'
        )

        shutil.copy2(unit_path, backup_path)
        self._logger.info('Backed up existing unit file to %s', backup_path)

        return backup_path

    async def validate_write_permissions(
        self,
        target_dir: Path,
    ) -> PermissionResult:
        """Validate write permissions for target directory.
        """
        try:
            if not target_dir.exists():
                # Check parent directory permissions
                parent_dir = target_dir.parent
                if not parent_dir.exists():
                    return PermissionResult(
                        has_permission=False,
                        required_permission='write',
                        error_message=(
                            f'Parent directory does not exist: {parent_dir}'
                        ),
                    )

                # Check if we can create the directory
                if not os.access(parent_dir, os.W_OK):
                    return PermissionResult(
                        has_permission=False,
                        required_permission='write',
                        error_message=f'No write permission: {target_dir}',
                    )
            else:
                # Check write permission on existing directory
                if not os.access(target_dir, os.W_OK):
                    return PermissionResult(
                        has_permission=False,
                        required_permission='write',
                        error_message=f'No write permission: {target_dir}',
                    )

            return PermissionResult(
                has_permission=True,
                required_permission='write',
            )

        except Exception as e:
            return PermissionResult(
                has_permission=False,
                required_permission='write',
                error_message=f'Permission check failed: {e}',
            )

    async def remove_unit_files(
        self,
        unit_name: str,
        system_level: bool,
    ) -> bool:
        """Remove timer and service unit files (for rollback).
        """
        try:
            timer_name = self._ensure_suffix(unit_name, '.timer')
            service_name = self._ensure_suffix(
                unit_name.removesuffix('.timer'),
                '.service',
            )

            timer_path = await self.get_unit_file_path(
                timer_name,
                system_level,
            )
            service_path = await self.get_unit_file_path(
                service_name,
                system_level,
            )

            removed_any = False

            if timer_path.exists():
                timer_path.unlink()
                removed_any = True
                self._logger.info('Removed timer file: %s', timer_path)

            if service_path.exists():
                service_path.unlink()
                removed_any = True
                self._logger.info('Removed service file: %s', service_path)

            return removed_any

        except Exception as e:
            self._logger.error(
                'Failed to remove unit files for %s: %s',
                unit_name,
                e,
                exc_info=True
            )
            return False

    def _ensure_suffix(self, name: str, suffix: str) -> str:
        """Ensure name has the specified suffix.
        """
        return name if name.endswith(suffix) else f'{name}{suffix}'
