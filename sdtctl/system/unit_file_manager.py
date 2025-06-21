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
            # Prepare file paths
            paths = await self._prepare_unit_file_paths(
                config.name,
                system_level,
            )

            # Extract paths with proper type checking
            timer_path = paths['timer']
            service_path = paths['service']

            if not isinstance(timer_path, Path) \
                or not isinstance(service_path, Path):
                raise ValueError(
                    'Invalid path types returned from preparation'
                )

            # Validate permissions
            target_dir = timer_path.parent
            permission_result = \
                await self.validate_write_permissions(target_dir)
            if not permission_result.has_permission:
                return UnitFileWriteResult(
                    success=False,
                    error_message=permission_result.error_message,
                )

            # Backup existing files
            backup_paths = await self._backup_existing_files(
                paths,
                system_level,
            )

            # Ensure target directory exists
            self._dir_manager.ensure_directory_exists(target_dir)

            # Write files atomically
            await self._write_files_atomically(
                timer_path,
                timer_content,
                service_path,
                service_content,
            )

            return UnitFileWriteResult(
                success=True,
                timer_path=timer_path,
                service_path=service_path,
                backup_paths=backup_paths if backup_paths else None,
            )

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

    async def _prepare_unit_file_paths(
        self,
        timer_name: str,
        system_level: bool,
    ) -> dict[str, Path | str]:
        """Prepare timer and service file paths.
        """
        timer_name = self._ensure_suffix(timer_name, '.timer')
        service_name = self._ensure_suffix(
            timer_name.removesuffix('.timer'),
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

        return {
            'timer': timer_path,
            'service': service_path,
            'timer_name': timer_name,
            'service_name': service_name,
        }

    async def _backup_existing_files(
        self,
        paths: dict[str, Path | str],
        system_level: bool,
    ) -> list[Path]:
        """Backup existing unit files if they exist.
        """
        backup_paths = []

        timer_name = paths.get('timer_name')
        service_name = paths.get('service_name')
        timer_path = paths.get('timer')
        service_path = paths.get('service')

        if (timer_name and isinstance(timer_path, Path) and
            await self.check_unit_file_exists(str(timer_name), system_level)):
            backup_path = await self.backup_existing_unit(timer_path)
            backup_paths.append(backup_path)

        if (service_name and isinstance(service_path, Path) and
            await self.check_unit_file_exists(
                str(service_name),
                system_level,
            )):
            backup_path = await self.backup_existing_unit(service_path)
            backup_paths.append(backup_path)

        return backup_paths

    async def _write_files_atomically(
        self,
        timer_path: Path,
        timer_content: str,
        service_path: Path,
        service_content: str,
    ) -> None:
        """Write files atomically using temporary files.
        """
        timer_temp = timer_path.with_suffix('.timer.tmp')
        service_temp = service_path.with_suffix('.service.tmp')

        try:
            # Write to temporary files
            timer_temp.write_text(timer_content, encoding='utf-8')
            service_temp.write_text(service_content, encoding='utf-8')

            # Atomic rename
            timer_temp.rename(timer_path)
            service_temp.rename(service_path)

            # Set permissions
            timer_path.chmod(0o644)
            service_path.chmod(0o644)

        except Exception as e:
            # Clean up temp files on error
            self._cleanup_temp_files([timer_temp, service_temp])
            raise e

    def _cleanup_temp_files(self, temp_files: list[Path]) -> None:
        """Clean up temporary files.
        """
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()

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

    async def write_unit_file(
        self,
        unit_name: str,
        content: str,
        system_level: bool,
    ) -> Path:
        """Write a single unit file.

        Args:
            unit_name: Name of the unit file (e.g., 'my-timer.timer')
            content: Content of the unit file
            system_level: Whether to write to system or user level

        Returns:
            Path to the written unit file

        Raises:
            Exception: If writing fails
        """
        unit_path = await self.get_unit_file_path(unit_name, system_level)
        target_dir = unit_path.parent

        # Validate permissions
        permission_result = await self.validate_write_permissions(target_dir)
        if not permission_result.has_permission:
            raise Exception(permission_result.error_message)

        # Backup existing file if it exists
        if unit_path.exists():
            await self.backup_existing_unit(unit_path)

        # Ensure target directory exists
        self._dir_manager.ensure_directory_exists(target_dir)

        # Write file atomically
        temp_path = unit_path.with_suffix(f'{unit_path.suffix}.tmp')

        try:
            temp_path.write_text(content, encoding='utf-8')
            temp_path.rename(unit_path)
            unit_path.chmod(0o644)

            self._logger.info(f'Successfully wrote unit file: {unit_path}')
            return unit_path

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            self._logger.error(f'Failed to write unit file {unit_name}: {e}')
            raise

    async def remove_unit_file(
        self,
        unit_name: str,
        system_level: bool,
    ) -> bool:
        """Remove a single unit file.

        Args:
            unit_name: Name of the unit file to remove
            system_level: Whether to remove from system or user level

        Returns:
            True if file was removed, False if it didn't exist

        Raises:
            Exception: If removal fails
        """
        try:
            unit_path = await self.get_unit_file_path(unit_name, system_level)

            if not unit_path.exists():
                self._logger.debug(f'Unit file does not exist: {unit_path}')
                return False

            unit_path.unlink()
            self._logger.info(f'Removed unit file: {unit_path}')
            return True

        except Exception as e:
            self._logger.error(f'Failed to remove unit file {unit_name}: {e}')
            raise
