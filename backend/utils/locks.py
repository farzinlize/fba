from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import anyio

from backend.common.exception import errors
from backend.core.path_conf import RELOAD_LOCK_FILE
from backend.database.redis import redis_client


@asynccontextmanager
async def acquire_distributed_reload_lock() -> AsyncGenerator[None, Any]:
    """Acquire distributed hot reload lock"""
    lock = redis_client.lock(
        'fba:reload_lock',
        timeout=300,  # Lock lifetime: 5 minutes
        blocking_timeout=60,  # Lock acquisition timeout: 60 seconds
    )
    if not await lock.acquire():
        raise errors.ServerError(msg='Timed out acquiring the hot reload lock; please try again later')

    # File lock notifying the file watcher to skip reload
    lock_path = anyio.Path(RELOAD_LOCK_FILE)
    await lock_path.touch()

    try:
        yield
    finally:
        await lock_path.unlink(missing_ok=True)
        if await lock.owned():
            await lock.release()
