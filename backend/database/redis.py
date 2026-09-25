import sys

from redis.asyncio import BlockingConnectionPool, Redis
from redis.exceptions import AuthenticationError, TimeoutError

from backend.common.log import log
from backend.core.conf import settings


class RedisCli(Redis):
    """Redis client"""

    def __init__(
        self,
        host: str = settings.REDIS_HOST,
        port: int = settings.REDIS_PORT,
        password: str = settings.REDIS_PASSWORD,
        db: int = settings.REDIS_DATABASE,
        socket_timeout: int | None = settings.REDIS_TIMEOUT,
        socket_connect_timeout: int = settings.REDIS_TIMEOUT,
        *,
        socket_keepalive: bool = True,
        health_check_interval: int = 30,
        decode_responses: bool = True,
        max_connections: int = settings.REDIS_MAX_CONNECTIONS,
        pool_timeout: int = settings.REDIS_POOL_TIMEOUT,
    ) -> None:
        """
        Initialize Redis client

        :param host: Redis server host address
        :param port: Redis server port
        :param password: Redis authentication password
        :param db: Redis logical database index
        :param socket_timeout: Socket read/write timeout
        :param socket_connect_timeout: TCP connection timeout
        :param socket_keepalive: Whether to enable TCP keepalive probes
        :param health_check_interval: Health check interval (seconds)
        :param decode_responses: Whether to decode Redis byte responses to UTF-8 strings automatically
        :param max_connections: Maximum pool connections; wait when exceeded instead of creating unlimited connections
        :param pool_timeout: Timeout waiting for an available connection (seconds)
        """
        pool = BlockingConnectionPool(
            max_connections=max_connections,
            timeout=pool_timeout,
            host=host,
            port=port,
            password=password,
            db=db,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            socket_keepalive=socket_keepalive,
            health_check_interval=health_check_interval,
            decode_responses=decode_responses,
        )
        super().__init__(connection_pool=pool)
        # The client exclusively owns the connection pool and releases it on aclose
        self.auto_close_connection_pool = True

    async def init(self) -> None:
        """Initialize Redis server connection"""
        try:
            await self.ping()
        except TimeoutError:
            log.error('Redis server connection timed out')
            sys.exit()
        except AuthenticationError:
            log.error('Redis server authentication failed')
            sys.exit()
        except Exception as e:
            log.error('Redis server connection error {}', e)
            sys.exit()

    async def delete_by_prefix(
        self,
        key_prefix: str,
        exclude_keys: str | list[str] | None = None,
        batch_size: int = 1000,
        count: int = 1000,
    ) -> None:
        """
        Delete all keys with the specified prefix

        :param key_prefix: Key prefix to delete
        :param exclude_keys: Key or list of keys to exclude
        :param batch_size: Deletion batch size
        :param count: Number of items per scan batch
        :return:
        """
        exclude_set = (
            set(exclude_keys)
            if isinstance(exclude_keys, list)
            else {exclude_keys}
            if isinstance(exclude_keys, str)
            else set()
        )
        batch_keys = []
        if key_prefix not in exclude_set and await self.exists(key_prefix):
            batch_keys.append(key_prefix)
        async for key in self.scan_iter(match=f'{key_prefix}:*', count=count):
            if key not in exclude_set:
                batch_keys.append(key)
                if len(batch_keys) >= batch_size:
                    await self.delete(*batch_keys)
                    batch_keys.clear()
        if batch_keys:
            await self.delete(*batch_keys)

    async def get_by_prefix(self, key_prefix: str, count: int = 1000) -> list[str]:
        """
        Get all keys with the specified prefix

        :param key_prefix: Key prefix to search for
        :param count: Items per scan batch; larger values scan faster but consume more server resources
        :return:
        """
        return [key async for key in self.scan_iter(match=f'{key_prefix}:*', count=count)]

    async def mget_batched(self, keys: list[str], batch_size: int = 1000) -> list[str | None]:
        """
        Get values of multiple keys in batches

        :param keys: Key list
        :param batch_size: Batch size
        :return:
        """
        if batch_size <= 0:
            raise ValueError('batch_size must be greater than 0')
        if not keys:
            return []
        values: list[str | None] = []
        for index in range(0, len(keys), batch_size):
            values.extend(await self.mget(keys[index : index + batch_size]))
        return values

    async def exists_batched(self, keys: list[str], batch_size: int = 1000) -> list[bool]:
        """
        Check existence of multiple keys in batches

        :param keys: Key list
        :param batch_size: Batch size
        :return:
        """
        if batch_size <= 0:
            raise ValueError('batch_size must be greater than 0')
        return [value is not None for value in await self.mget_batched(keys, batch_size=batch_size)]

    async def smembers_many(self, keys: list[str], batch_size: int = 100) -> list[set[str]]:
        """
        Get members of multiple sets in batches

        :param keys: Key list
        :param batch_size: Batch size
        :return:
        """
        if batch_size <= 0:
            raise ValueError('batch_size must be greater than 0')
        if not keys:
            return []
        members: list[set[str]] = []
        for index in range(0, len(keys), batch_size):
            batch = keys[index : index + batch_size]
            async with self.pipeline(transaction=False) as pipe:
                for key in batch:
                    pipe.smembers(key)
                results = await pipe.execute()
            members.extend(set(result) if result else set() for result in results)
        return members

    async def delete_batched(self, keys: list[str], batch_size: int = 1000) -> int:
        """
        Delete multiple keys in batches

        :param keys: Key list
        :param batch_size: Batch size
        :return:
        """
        if batch_size <= 0:
            raise ValueError('batch_size must be greater than 0')
        if not keys:
            return 0
        deleted = 0
        for index in range(0, len(keys), batch_size):
            batch = keys[index : index + batch_size]
            deleted += await self.delete(*batch)
        return deleted


# Create Redis client singleton
redis_client: RedisCli = RedisCli()
