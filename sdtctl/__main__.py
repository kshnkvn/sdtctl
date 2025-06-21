import asyncio

from sdtctl.config import setup_logger


async def main() -> None:
    """The main entry point for the application.
    """
    setup_logger()


if __name__ == '__main__':
    asyncio.run(main())
