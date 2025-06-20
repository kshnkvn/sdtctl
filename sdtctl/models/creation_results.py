from pathlib import Path

from pydantic import BaseModel


class TimerCreationResult(BaseModel):
    """Result of timer creation operation.
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
    """
    model_config = {'frozen': True}

    timer_content: str
    service_content: str
    timer_path: Path
    service_path: Path


class PermissionResult(BaseModel):
    """Result of permission check.
    """
    model_config = {'frozen': True}

    has_permission: bool
    required_permission: str
    error_message: str | None = None


class UnitFileWriteResult(BaseModel):
    """Result of unit file write operation.
    """
    model_config = {'frozen': True}

    success: bool
    timer_path: Path | None = None
    service_path: Path | None = None
    backup_paths: list[Path] | None = None
    error_message: str | None = None


class TimerInstallationResult(BaseModel):
    """Result of timer installation via systemd.
    """
    model_config = {'frozen': True}

    success: bool
    timer_name: str
    enabled: bool
    state: str | None = None
    error_message: str | None = None
