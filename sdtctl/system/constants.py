from enum import StrEnum


class SystemdPaths(StrEnum):
    """Systemd directory paths.
    """

    # System-level unit directories
    SYSTEM_UNIT_DIR = '/etc/systemd/system'

    # User-level unit directories (relative to home)
    USER_CONFIG_DIR = '.config/systemd/user'

    # Backup directories
    SYSTEM_BACKUP_DIR = '/var/backups/systemd'
    USER_BACKUP_DIR = '.local/share/systemd/backups'
