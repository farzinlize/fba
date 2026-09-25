import asyncio
import datetime
import os
import threading
import time

from dataclasses import dataclass

from backend.common.dataclasses import SnowflakeInfo
from backend.common.exception import errors
from backend.common.log import log
from backend.core.conf import settings
from backend.database.redis import redis_client
from backend.utils.timezone import timezone


@dataclass(frozen=True)
class SnowflakeConfig:
    """Snowflake configuration using the original Twitter Snowflake 64-bit ID allocation"""

    # Bit allocation
    WORKER_ID_BITS: int = 5
    DATACENTER_ID_BITS: int = 5
    SEQUENCE_BITS: int = 12

    # Maximum values
    MAX_WORKER_ID: int = (1 << WORKER_ID_BITS) - 1  # 31
    MAX_DATACENTER_ID: int = (1 << DATACENTER_ID_BITS) - 1  # 31
    SEQUENCE_MASK: int = (1 << SEQUENCE_BITS) - 1  # 4095

    # Bit shift offsets
    WORKER_ID_SHIFT: int = SEQUENCE_BITS
    DATACENTER_ID_SHIFT: int = SEQUENCE_BITS + WORKER_ID_BITS
    TIMESTAMP_LEFT_SHIFT: int = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

    # Epoch timestamp
    EPOCH: int = 1262275200000

    # Clock rollback tolerance for normal NTP adjustments (nonstandard)
    CLOCK_BACKWARD_TOLERANCE_MS: int = 10_000


class SnowflakeNodeManager:
    """Snowflake node manager allocating and managing node IDs through Redis"""

    def __init__(self) -> None:
        """Initialize node manager"""
        self.datacenter_id: int | None = None
        self.worker_id: int | None = None
        self.node_redis_prefix: str = f'{settings.SNOWFLAKE_REDIS_PREFIX}:nodes'
        self._heartbeat_task: asyncio.Task | None = None

    async def acquire_node_id(self) -> tuple[int, int]:
        """Acquire available datacenter_id and worker_id from Redis"""
        occupied_nodes = set()
        async for key in redis_client.scan_iter(match=f'{self.node_redis_prefix}:*', count=1000):
            parts = key.split(':')
            if len(parts) >= 5:
                try:
                    datacenter_id = int(parts[-2])
                    worker_id = int(parts[-1])
                    occupied_nodes.add((datacenter_id, worker_id))
                except ValueError:
                    continue

        # Find the first available ID pair sequentially
        for datacenter_id in range(SnowflakeConfig.MAX_DATACENTER_ID + 1):
            for worker_id in range(SnowflakeConfig.MAX_WORKER_ID + 1):
                if (datacenter_id, worker_id) not in occupied_nodes and await self._register(datacenter_id, worker_id):
                    return datacenter_id, worker_id

        raise errors.ServerError(msg='No Snowflake nodes available; all nodes are allocated')

    async def _register(self, datacenter_id: int, worker_id: int) -> bool:
        key = f'{self.node_redis_prefix}:{datacenter_id}:{worker_id}'
        value = f'pid:{os.getpid()}-ts:{timezone.now().timestamp()}'
        return await redis_client.set(key, value, nx=True, ex=settings.SNOWFLAKE_NODE_TTL_SECONDS)

    async def start_heartbeat(self, datacenter_id: int, worker_id: int) -> None:
        """Start node heartbeat"""
        self.datacenter_id = datacenter_id
        self.worker_id = worker_id

        async def heartbeat() -> None:
            key = f'{self.node_redis_prefix}:{datacenter_id}:{worker_id}'
            while True:
                await asyncio.sleep(settings.SNOWFLAKE_HEARTBEAT_INTERVAL_SECONDS)
                try:
                    await redis_client.expire(key, settings.SNOWFLAKE_NODE_TTL_SECONDS)
                    log.debug(f'Snowflake node heartbeat started: datacenter_id={datacenter_id}, worker_id={worker_id}')
                except Exception as e:
                    log.error(f'Snowflake node heartbeat failed: {e}')

        self._heartbeat_task = asyncio.create_task(heartbeat())

    async def release(self) -> None:
        """Release node"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                log.debug(
                    f'Snowflake node heartbeat released: datacenter_id={self.datacenter_id}, worker_id={self.worker_id}'
                )

        if self.datacenter_id is not None and self.worker_id is not None:
            key = f'{self.node_redis_prefix}:{self.datacenter_id}:{self.worker_id}'
            await redis_client.delete(key)


class Snowflake:
    """Snowflake ID generator"""

    def __init__(self) -> None:
        """Initialize Snowflake generator"""
        self.datacenter_id: int | None = None
        self.worker_id: int | None = None
        self.sequence: int = 0
        self.last_timestamp: int = -1

        self._lock = threading.Lock()
        self._init_lock = asyncio.Lock()
        self._initialized = False
        self._node_manager: SnowflakeNodeManager | None = None
        self._auto_allocated = False  # Track whether IDs were allocated automatically by Redis

    async def init(self) -> None:
        """Initialize Snowflake generator"""
        if self._initialized:
            return

        # Initialization performs Redis I/O; use asyncio.Lock because threading.Lock blocks the event loop during await
        async with self._init_lock:
            if self._initialized:
                return

            # Fixed allocation through environment variables
            if settings.SNOWFLAKE_DATACENTER_ID is not None and settings.SNOWFLAKE_WORKER_ID is not None:
                self.datacenter_id = settings.SNOWFLAKE_DATACENTER_ID
                self.worker_id = settings.SNOWFLAKE_WORKER_ID
                log.debug(
                    f'Snowflake uses fixed nodes from environment variables: '
                    f'datacenter_id={self.datacenter_id}, worker_id={self.worker_id}'
                )
            elif (settings.SNOWFLAKE_DATACENTER_ID is not None and settings.SNOWFLAKE_WORKER_ID is None) or (
                settings.SNOWFLAKE_DATACENTER_ID is None and settings.SNOWFLAKE_WORKER_ID is not None
            ):
                log.error(
                    'Invalid Snowflake datacenter_id and worker_id configuration; both must be set or both must be None'
                )
                raise errors.ServerError(msg='Snowflake configuration failed; contact the system administrator')
            else:
                # Dynamic allocation through Redis
                self._node_manager = SnowflakeNodeManager()
                self.datacenter_id, self.worker_id = await self._node_manager.acquire_node_id()
                self._auto_allocated = True
                await self._node_manager.start_heartbeat(self.datacenter_id, self.worker_id)
                log.debug(
                    f'Snowflake uses nodes dynamically allocated by Redis: '
                    f'datacenter_id={self.datacenter_id}, worker_id={self.worker_id}'
                )

            # Validate range strictly
            if not (0 <= self.datacenter_id <= SnowflakeConfig.MAX_DATACENTER_ID):
                log.error(f'Invalid Snowflake datacenter_id; must be between 0 and {SnowflakeConfig.MAX_DATACENTER_ID}')
                raise errors.ServerError(
                    msg='Snowflake datacenter configuration failed; contact the system administrator'
                )
            if not (0 <= self.worker_id <= SnowflakeConfig.MAX_WORKER_ID):
                log.error(f'Invalid Snowflake worker_id; must be between 0 and {SnowflakeConfig.MAX_WORKER_ID}')
                raise errors.ServerError(msg='Snowflake worker configuration failed; contact the system administrator')

            self._initialized = True

    async def shutdown(self) -> None:
        """Release Redis node"""
        if self._node_manager and self._auto_allocated:
            await self._node_manager.release()

    @staticmethod
    def _current_ms() -> int:
        return int(timezone.now().timestamp() * 1000)

    def _till_next_ms(self, last_timestamp: int) -> int:
        """Wait until the next millisecond"""
        ts = self._current_ms()
        while ts <= last_timestamp:
            time.sleep(0.0001)
            ts = self._current_ms()
        return ts

    def generate(self) -> int:
        """Generate Snowflake ID"""
        if not self._initialized:
            raise errors.ServerError(msg='Failed to generate Snowflake ID: generator is not initialized')

        with self._lock:
            timestamp = self._current_ms()

            # Handle clock rollback
            if timestamp < self.last_timestamp:
                back_ms = self.last_timestamp - timestamp
                if back_ms <= SnowflakeConfig.CLOCK_BACKWARD_TOLERANCE_MS:
                    log.warning(f'Clock rollback of {back_ms} ms detected; waiting for recovery...')
                    timestamp = self._till_next_ms(self.last_timestamp)
                else:
                    raise errors.ServerError(
                        msg=(
                            f'Failed to generate Snowflake ID: clock rollback exceeds {back_ms} ms; contact the '
                            f'system administrator immediately'
                        )
                    )

            # Increment sequence within the same millisecond
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & SnowflakeConfig.SEQUENCE_MASK
                if self.sequence == 0:
                    timestamp = self._till_next_ms(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # Assemble 64-bit ID
            return (
                ((timestamp - SnowflakeConfig.EPOCH) << SnowflakeConfig.TIMESTAMP_LEFT_SHIFT)
                | (self.datacenter_id << SnowflakeConfig.DATACENTER_ID_SHIFT)
                | (self.worker_id << SnowflakeConfig.WORKER_ID_SHIFT)
                | self.sequence
            )

    @staticmethod
    def parse(snowflake_id: int) -> SnowflakeInfo:
        """
        Parse Snowflake ID and extract its components

        :param snowflake_id: Snowflake ID
        :return:
        """
        timestamp = (snowflake_id >> SnowflakeConfig.TIMESTAMP_LEFT_SHIFT) + SnowflakeConfig.EPOCH
        datacenter_id = (snowflake_id >> SnowflakeConfig.DATACENTER_ID_SHIFT) & SnowflakeConfig.MAX_DATACENTER_ID
        worker_id = (snowflake_id >> SnowflakeConfig.WORKER_ID_SHIFT) & SnowflakeConfig.MAX_WORKER_ID
        sequence = snowflake_id & SnowflakeConfig.SEQUENCE_MASK

        return SnowflakeInfo(
            timestamp=timestamp,
            datetime=timezone.to_str(datetime.datetime.fromtimestamp(timestamp / 1000, timezone.tz_info)),
            datacenter_id=datacenter_id,
            worker_id=worker_id,
            sequence=sequence,
        )


snowflake = Snowflake()
