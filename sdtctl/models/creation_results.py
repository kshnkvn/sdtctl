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
