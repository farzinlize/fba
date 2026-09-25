import asyncio
import json

from backend.common.cache.local import local_cache_manager
from backend.common.log import log
from backend.core.conf import settings
from backend.database.redis import RedisCli, redis_client


class CachePubSubManager:
    """Cache Pub/Sub manager"""

    _pubsub_task: asyncio.Task | None = None

    @staticmethod
    async def publish_invalidation(cache_key: str, *, delete_by_prefix: bool) -> None:
        """
        Publish cache invalidation notification

        :param cache_key: Cache key
        :param delete_by_prefix: Whether to delete all cache entries matching the prefix
        :return:
        """
        try:
            message = json.dumps({'cache_key': cache_key, 'delete_by_prefix': delete_by_prefix})
            await redis_client.publish(settings.CACHE_PUBSUB_CHANNEL, message)
        except Exception as e:
            log.warning(f'[CachePubSub] Failed to publish notification: {e}')

    @staticmethod
    async def subscribe_and_listen() -> None:  # ruff:ignore[complex-structure]
        """Subscribe to and listen for cache invalidation notifications"""
        reconnect_attempts = 0

        while reconnect_attempts < settings.CACHE_PUBSUB_MAX_RECONNECT_ATTEMPTS:
            pubsub_client: RedisCli | None = None
            pubsub = None

            try:
                # Use a dedicated connection
                pubsub_client = RedisCli(max_connections=1)
                pubsub = pubsub_client.pubsub()
                await pubsub.subscribe(settings.CACHE_PUBSUB_CHANNEL)

                # Subscription successful
                reconnect_attempts = 0

                # Poll with a timeout instead of listen(); each read triggers a health-check PING,
                # preventing the coroutine from hanging indefinitely after a silent disconnection
                while True:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=settings.CACHE_PUBSUB_POLL_TIMEOUT,
                    )
                    if message is None or message['type'] != 'message':
                        continue
                    try:
                        data = json.loads(message['data'])
                        cache_key = data['cache_key']
                        if not data['delete_by_prefix']:
                            local_cache_manager.delete(cache_key)
                        else:
                            local_cache_manager.delete_by_prefix(cache_key)
                    except json.JSONDecodeError as e:
                        log.warning(f'[CachePubSub] Invalid message format: {e}')
                    except Exception as e:
                        log.error(f'[CachePubSub] Failed to process notification: {e}')

            except asyncio.CancelledError:
                break
            except Exception as e:
                reconnect_attempts += 1
                log.error(
                    f'[CachePubSub] Subscription error '
                    f'({reconnect_attempts}/{settings.CACHE_PUBSUB_MAX_RECONNECT_ATTEMPTS}): {e}'
                )

                if reconnect_attempts >= settings.CACHE_PUBSUB_MAX_RECONNECT_ATTEMPTS:
                    log.error('[CachePubSub] Maximum reconnection attempts reached; stopping subscription')
                    break

                await asyncio.sleep(settings.CACHE_PUBSUB_RECONNECT_DELAY)
            finally:
                if pubsub_client:
                    try:
                        await pubsub_client.aclose()
                    except Exception:
                        pass
                if pubsub:
                    try:
                        await pubsub.aclose()
                    except Exception:
                        pass

    @classmethod
    def start_listener(cls) -> None:
        """Start cache Pub/Sub listener"""
        if not settings.CACHE_LOCAL_ENABLED:
            return

        if cls._pubsub_task is None or cls._pubsub_task.done():
            cls._pubsub_task = asyncio.create_task(cls.subscribe_and_listen())

    @classmethod
    async def stop_listener(cls) -> None:
        """Stop cache Pub/Sub listener"""
        if cls._pubsub_task is None:
            return

        if not cls._pubsub_task.done():
            cls._pubsub_task.cancel()
            try:
                await cls._pubsub_task
            except asyncio.CancelledError:
                pass

        cls._pubsub_task = None


cache_pubsub_manager = CachePubSubManager()
