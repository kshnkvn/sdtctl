from pathlib import Path

from sdtctl.utils import BaseModel


class TimerCreationResult(BaseModel):
    """Result of timer creation operation.

    Args:
        success: Whether the operation was successful
        timer_name: Name of the timer that was created
        timer_path: Path to the created timer unit file
        service_path: Path to the created service unit file
        enabled: Whether the timer was enabled
        started: Whether the timer was started
        error_message: Error message if the operation failed
        warnings: List of warning messages
    """
    model_config = {'frozen': True}

    success: bool
    timer_name: str
    timer_path: Path | None = None
    service_path: Path | None = None
    enabled: bool = False
    started: bool = False
    error_message: str | None = None
    warnings: list[str] | None = None


class UnitPreview(BaseModel):
    """Preview of generated unit files.

    Args:
        timer_content: Content of the timer unit file
        service_content: Content of the service unit file
        timer_path: Path where the timer file will be created
        service_path: Path where the service file will be created
    """
    model_config = {'frozen': True}

    timer_content: str
    service_content: str
    timer_path: Path
    service_path: Path


class PermissionResult(BaseModel):
    """Result of permission check.

    Args:
        has_permission: Whether the required permission is available
        required_permission: Description of the required permission
        error_message: Error message if permission check failed
    """
    model_config = {'frozen': True}

    has_permission: bool
    required_permission: str
    error_message: str | None = None


class UnitFileWriteResult(BaseModel):
    """Result of unit file write operation.

    Args:
        success: Whether the write operation was successful
        timer_path: Path to the written timer unit file
        service_path: Path to the written service unit file
        backup_paths: List of backup file paths created
        error_message: Error message if write operation failed
    """
    model_config = {'frozen': True}

    success: bool
    timer_path: Path | None = None
    service_path: Path | None = None
    backup_paths: list[Path] | None = None
    error_message: str | None = None


class TimerInstallationResult(BaseModel):
    """Result of timer installation via systemd.

    Args:
        success: Whether the installation was successful
        timer_name: Name of the installed timer
        enabled: Whether the timer was enabled
        state: Current state of the timer
        error_message: Error message if installation failed
    """
    model_config = {'frozen': True}

    success: bool
    timer_name: str
    enabled: bool
    state: str | None = None
    error_message: str | None = None
