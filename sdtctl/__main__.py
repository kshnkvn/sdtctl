import asyncio

from sdtctl.config import setup_logger
from sdtctl.systemd.connection import DBusConnectionManager
from sdtctl.tui.app import SdtctlApp


async def main() -> None:
    """The main entry point for the application.
    """
    setup_logger()

    dbus_manager = DBusConnectionManager.get_instance()
    app = SdtctlApp()

    try:
        await app.run_async()
    finally:
        await dbus_manager.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
