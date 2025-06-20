import asyncio
import logging
import threading
from typing import Self

from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType
from dbus_next.errors import DBusError

from sdtctl.dbus.constants import ConnectionConfig, DBusConstants


class SingletonMeta(type):
    """Metaclass that creates a singleton instance.
    """

    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class DBusConnectionManager(metaclass=SingletonMeta):
    """Manages the D-Bus connection with automatic reconnection.
    """

    def __init__(
        self,
        bus_type: BusType = BusType.SYSTEM,
        max_retries: int = ConnectionConfig.DEFAULT_MAX_RETRIES,
        initial_backoff: float = ConnectionConfig.DEFAULT_INITIAL_BACKOFF,
    ):
        """
        Initializes the DBusConnectionManager.

        Args:
            bus_type: The D-Bus bus type to connect to.
            max_retries: The maximum number of connection retries.
            initial_backoff: The initial backoff delay in seconds for retries.
        """
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized'):
            return

        self._logger = logging.getLogger(__name__)

        self._bus_type = bus_type
        self._bus: MessageBus | None = None
        self._max_retries = max_retries
        self._initial_backoff = initial_backoff
        self._connection_lock = asyncio.Lock()
        self._initialized = True

    async def connect(self) -> None:
        """Connects to the D-Bus with an exponential backoff retry mechanism.
        """
        async with self._connection_lock:
            if self._is_already_connected():
                self._logger.debug('Already connected to D-Bus.')
                return

            await self._attempt_connection_with_retry()

    def _is_already_connected(self) -> bool:
        """Check if already connected to D-Bus.
        """
        return self._bus is not None and self._bus.connected

    async def _attempt_connection_with_retry(self) -> None:
        """Attempt connection with exponential backoff retry logic.
        """
        retries = 0
        backoff = self._initial_backoff

        while retries < self._max_retries:
            if await self._try_single_connection_attempt(retries + 1):
                return

            await self._handle_connection_failure(backoff)
            retries += 1
            backoff *= ConnectionConfig.BACKOFF_MULTIPLIER

        self._raise_connection_failure()

    async def _try_single_connection_attempt(
        self,
        attempt_number: int,
    ) -> bool:
        """Try a single connection attempt.

        Args:
            attempt_number: The current attempt number for logging.

        Returns:
            True if connection was successful, False otherwise.
        """
        try:
            self._logger.info(
                'Attempting to connect to D-Bus (attempt %d/%d)...',
                attempt_number,
                self._max_retries,
            )
            self._bus = await MessageBus(bus_type=self._bus_type).connect()
            self._logger.info('Successfully connected to D-Bus.')
            return True
        except DBusError as e:
            self._logger.warning('Failed to connect to D-Bus: %s', e)
            return False
        except Exception as e:
            self._logger.error(
                'An unexpected error occurred during D-Bus connection: %s',
                e,
                exc_info=True,
            )
            return False

    async def _handle_connection_failure(self, backoff: float) -> None:
        """Handle connection failure by waiting for backoff period.
        """
        self._logger.info('Retrying in %.2f seconds.', backoff)
        await asyncio.sleep(backoff)

    def _raise_connection_failure(self) -> None:
        """Raise connection failure exception after all retries exhausted.
        """
        self._logger.critical(
            'Could not connect to D-Bus after %d attempts.',
            self._max_retries,
        )
        raise ConnectionError(
            f'Failed to connect to D-Bus after {self._max_retries} attempts.'
        )

    async def disconnect(self) -> None:
        """Disconnects from the D-Bus if connected.
        """
        async with self._connection_lock:
            if self._bus:
                self._logger.info('Disconnecting from D-Bus.')
                self._bus.disconnect()
                self._bus = None

    async def get_bus(self) -> MessageBus:
        """Returns the MessageBus object, ensuring a connection is established.

        If the connection is lost, it will attempt to reconnect.

        Returns:
            The connected MessageBus object.

        Raises:
            ConnectionError: If a connection cannot be established.
        """
        if not await self.health_check():
            self._logger.warning(
                'D-Bus connection is down. Attempting to reconnect.'
            )
            await self.connect()

        if not self._bus:
            # This should not be reached if connect() is successful
            raise ConnectionError('Failed to get a valid D-Bus connection.')

        return self._bus

    async def health_check(self) -> bool:
        """Verifies the D-Bus connection status.

        Returns:
            True if the connection is healthy, False otherwise.
        """
        if not self._is_already_connected():
            return False

        try:
            return await self._perform_health_check_call()
        except DBusError as e:
            self._logger.warning('D-Bus health check failed: %s', e)
            return False
        except Exception:
            self._logger.exception(
                'Unexpected error during D-Bus health check.'
            )
            return False

    async def _perform_health_check_call(self) -> bool:
        """Perform the actual D-Bus health check call.
        """
        # A lightweight call to check if the bus is responsive.
        introspection = await self._bus.introspect(  # type: ignore
            DBusConstants.SERVICE_NAME,
            DBusConstants.OBJECT_PATH,
        )
        proxy = self._bus.get_proxy_object(  # type: ignore
            DBusConstants.SERVICE_NAME,
            DBusConstants.OBJECT_PATH,
            introspection,
        )
        interface = proxy.get_interface(DBusConstants.INTERFACE)
        await interface.call_get_id()  # type: ignore
        return True

    @classmethod
    def get_instance(cls) -> Self:
        """Returns the singleton instance of DBusConnectionManager.

        Returns:
            The singleton instance.
        """
        return cls()
