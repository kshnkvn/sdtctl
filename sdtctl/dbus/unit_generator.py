import logging

from sdtctl.models.timer_config import (
    ServiceConfig,
    TimerCreationConfig,
    TimerSchedule,
)


class SystemdUnitGenerator:
    """Generates systemd unit files from Pydantic configuration objects.
    """

    def __init__(self) -> None:
        """Initialize the unit generator.
        """
        self._logger = logging.getLogger(__name__)

    def generate_timer_unit(self, config: TimerCreationConfig) -> str:
        """Generate .timer unit file content.
        """
        sections = []

        # [Unit] section
        sections.append(self._format_unit_section(
            config.description,
            f'Timer for {config.name}'
        ))

        # [Timer] section
        sections.append(self._format_timer_section(config.timer_schedule))

        # [Install] section
        sections.append(self._format_install_section(config.enabled))

        return '\n\n'.join(sections) + '\n'

    def generate_service_unit(self, config: TimerCreationConfig) -> str:
        """Generate .service unit file content.
        """
        sections = []

        # [Unit] section
        sections.append(self._format_unit_section(
            f'Service for {config.description}',
            f'Service unit for {config.name} timer',
        ))

        # [Service] section
        sections.append(self._format_service_section(config.service_config))

        return '\n\n'.join(sections) + '\n'

    def validate_generated_unit(self, unit_content: str) -> bool:
        """Validate generated unit file syntax.
        """
        validator = UnitFileValidator()

        # Check if it's a timer or service unit
        if '[Timer]' in unit_content:
            return validator.validate_timer_unit(unit_content)
        elif '[Service]' in unit_content:
            return validator.validate_service_unit(unit_content)
        else:
            self._logger.warning('Unknown unit type for validation')
            return False

    def _format_timer_section(self, schedule: TimerSchedule) -> str:
        """Format [Timer] section content.
        """
        lines = ['[Timer]']

        # Calendar specification
        if schedule.calendar_spec:
            lines.append(f'OnCalendar={schedule.calendar_spec}')

        # Monotonic schedules
        if schedule.on_boot_sec is not None:
            lines.append(f'OnBootSec={schedule.on_boot_sec}')
        if schedule.on_startup_sec is not None:
            lines.append(f'OnStartupSec={schedule.on_startup_sec}')
        if schedule.on_unit_active_sec is not None:
            lines.append(f'OnUnitActiveSec={schedule.on_unit_active_sec}')
        if schedule.on_unit_inactive_sec is not None:
            lines.append(f'OnUnitInactiveSec={schedule.on_unit_inactive_sec}')

        # Timer behavior
        if schedule.accuracy_sec != 60:  # Only if not default
            lines.append(f'AccuracySec={schedule.accuracy_sec}')
        if schedule.randomized_delay_sec > 0:
            lines.append(f'RandomizedDelaySec={schedule.randomized_delay_sec}')
        if schedule.persistent:
            lines.append('Persistent=true')
        if schedule.wake_system:
            lines.append('WakeSystem=true')
        if not schedule.remain_after_elapse:  # Only if not default
            lines.append('RemainAfterElapse=false')

        return '\n'.join(lines)

    def _format_service_section(self, service: ServiceConfig) -> str:
        """Format [Service] section content.
        """
        lines = ['[Service]']

        # Service type
        lines.append(f'Type={service.type.value}')

        # Execution command
        lines.append(f'ExecStart={service.exec_start}')

        # User and group
        if service.user:
            lines.append(f'User={service.user}')
        if service.group:
            lines.append(f'Group={service.group}')

        # Working directory
        if service.working_directory:
            lines.append(f'WorkingDirectory={service.working_directory}')

        # Environment variables
        if service.environment:
            for key, value in service.environment.items():
                lines.append(f'Environment="{key}={value}"')

        # Restart policy
        if service.restart.value != 'no':
            lines.append(f'Restart={service.restart.value}')

        return '\n'.join(lines)

    def _format_unit_section(
        self,
        description: str,
        documentation: str = '',
    ) -> str:
        """Format [Unit] section content.
        """
        lines = ['[Unit]']
        lines.append(f'Description={description}')

        if documentation:
            lines.append(f'Documentation={documentation}')

        return '\n'.join(lines)

    def _format_install_section(self, enabled: bool = True) -> str:
        """Format [Install] section content.
        """
        lines = ['[Install]']
        lines.append('WantedBy=timers.target')
        return '\n'.join(lines)


class UnitFileValidator:
    """Validates systemd unit file syntax and content.
    """

    def __init__(self) -> None:
        """Initialize the validator.
        """
        self._logger = logging.getLogger(__name__)

    def validate_timer_unit(self, content: str) -> bool:
        """Validate timer unit file syntax.
        """
        missing_sections = self.check_required_sections(content, 'timer')
        if missing_sections:
            self._logger.error(
                'Timer unit missing required sections: %s',
                ', '.join(missing_sections)
            )
            return False

        # Check for at least one timer specification
        timer_section = self._extract_section(content, 'Timer')
        if not timer_section:
            return False

        has_timer_spec = any(
            line.startswith(spec) for spec in [
                'OnCalendar=',
                'OnBootSec=',
                'OnStartupSec=',
                'OnUnitActiveSec=',
                'OnUnitInactiveSec='
            ]
            for line in timer_section
        )

        if not has_timer_spec:
            self._logger.error('Timer unit has no timer specifications')
            return False

        return True

    def validate_service_unit(self, content: str) -> bool:
        """Validate service unit file syntax.
        """
        missing_sections = self.check_required_sections(content, 'service')
        if missing_sections:
            self._logger.error(
                'Service unit missing required sections: %s',
                ', '.join(missing_sections)
            )
            return False

        # Check for ExecStart
        service_section = self._extract_section(content, 'Service')
        if not service_section:
            return False

        has_exec_start = any(
            line.startswith('ExecStart=') for line in service_section
        )

        if not has_exec_start:
            self._logger.error('Service unit missing ExecStart')
            return False

        return True

    def check_required_sections(
        self,
        content: str,
        unit_type: str,
    ) -> list[str]:
        """Check for required sections and return missing ones.
        """
        required_sections = {
            'timer': ['[Unit]', '[Timer]', '[Install]'],
            'service': ['[Unit]', '[Service]']
        }

        missing = []
        for section in required_sections.get(unit_type, []):
            if section not in content:
                missing.append(section)

        return missing

    def _extract_section(
        self,
        content: str,
        section_name: str,
    ) -> list[str] | None:
        """Extract lines from a specific section.
        """
        lines = content.split('\n')
        section_start = f'[{section_name}]'

        try:
            start_idx = lines.index(section_start)
        except ValueError:
            return None

        section_lines = []
        for line in lines[start_idx + 1:]:
            if line.startswith('[') and line.endswith(']'):
                break
            if line.strip():
                section_lines.append(line.strip())

        return section_lines
