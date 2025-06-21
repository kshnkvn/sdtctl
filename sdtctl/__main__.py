import sys

from sdtctl.cli import run_cli
from sdtctl.config import setup_logger


def main() -> None:
    """The main entry point for the application.
    """
    setup_logger()

    if len(sys.argv) > 1:
        # CLI mode - arguments provided
        run_cli()
    else:
        # TUI mode - no arguments provided
        print('TUI mode is not yet implemented.')


if __name__ == '__main__':
    main()
