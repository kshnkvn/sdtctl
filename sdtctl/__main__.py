from sdtctl.config import setup_logger
from sdtctl.tui.app import SdtctlApp


def main() -> None:
    """The main entry point for the application.
    """
    setup_logger()

    app = SdtctlApp()
    app.run()


if __name__ == '__main__':
    main()
