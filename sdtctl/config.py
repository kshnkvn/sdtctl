import logging

from systemd.journal import JournalHandler


def setup_logger() -> None:
    """Configure logging to use systemd journal.
    """
    app_logger = logging.getLogger('sdtctl')
    app_logger.setLevel(logging.DEBUG)

    journal_handler = JournalHandler(SYSLOG_IDENTIFIER='sdtctl')

    app_logger.addHandler(journal_handler)
