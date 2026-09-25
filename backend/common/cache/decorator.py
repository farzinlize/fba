import functools

from collections.abc import Awaitable, Callable, Sequence
from inspect import isawaitable
from typing import Any, ParamSpec, TypeVar

from msgspec import json

from backend.common.cache.local import local_cache_manager
from backend.common.cache.pubsub import cache_pubsub_manager
from backend.common.context import ctx
from backend.common.exception import errors
from backend.common.log import log
from backend.core.conf import settings
from backend.database.redis import redis_client
from backend.utils.serializers import select_columns_serialize, select_list_serialize

P = ParamSpec('P')
T = TypeVar('T')
_MISSING = object()


async def _build_cache_key(
    namespace: str,
    key: str | None,
    key_builder: Callable[..., str | Awaitable[str]] | None,
    *args: Any,
    **kwargs: Any,
) -> str:
    """Build cache key"""
    if key:
        if '.' in key:
            param, field = key.split('.', 1)
            value = kwargs.get(param, _MISSING)
            if value is _MISSING:
                raise errors.ServerError(msg=f'Failed to build cache key: parameter "{param}" does not exist')

            if isinstance(value, list):
                raise errors.ServerError(
                    msg=(
                        'Failed to build cache key: extracting fields from lists is unsupported; use '
                        'key_builder for list arguments'
                    )
                )

            if hasattr(value, field):
                value = getattr(value, field)
            elif isinstance(value, dict) and field in value:
                value = value[field]
            else:
                raise errors.ServerError(msg=f'Failed to build cache key: field "{field}" does not exist on the object')
        else:
            value = kwargs.get(key, _MISSING)
            if value is _MISSING:
                raise errors.ServerError(msg=f'Failed to build cache key: parameter "{key}" does not exist')

        return f'{namespace}:{value if value is not None else "none"}'

    if key_builder:
        value = key_builder(*args, **kwargs)
        if isawaitable(value):
            value = await value
        return f'{namespace}:{value}'

    return namespace


def _serialize_result(result: Any) -> bytes:
    """
    Serialize cached result

    :param result: Result to serialize
    :return:
    """
    # SQLAlchemy query table
    if hasattr(result, '__table__'):
        return json.encode(select_columns_serialize(result))

    # SQLAlchemy query list
    if (
        isinstance(result, Sequence)
        and not isinstance(result, (str, bytes))
        and len(result) > 0
        and hasattr(result[0], '__table__')
    ):
        return json.encode(select_list_serialize(result))

    # Primitive types
    return json.encode(result)


def _deserialize_result(value: bytes) -> Any:
    """
    Deserialize cached result

    :param value: Cached result
    :return:
    """
    try:
        return json.decode(value)
    except Exception:
        return value


def user_key_builder() -> str:
    """Generate cache key from the current user ID"""
    user_id = ctx.user_id
    if user_id is None:
        raise errors.ServerError(msg='Failed to build user cache key')
    return str(user_id)


def cached(  # ruff:ignore[complex-structure]
    namespace: str,
    *,
    key: str | None = None,
    key_builder: Callable[..., str | Awaitable[str]] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Caching decorator

    :param namespace: Cache namespace (usually the cache key prefix)
    :param key: Use the named method argument as the cache key; mutually exclusive with key_builder
    :param key_builder: Custom key builder function; mutually exclusive with key
    :return:
    """
    if key is not None and key_builder is not None:
        raise errors.ServerError(msg='key and key_builder cannot be used together')

    def decorator(func: Callable[P, T]) -> Callable[P, T]:  # ruff:ignore[complex-structure]
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cache_key = await _build_cache_key(namespace, key, key_builder, *args, **kwargs)

            # L1: local cache
            if settings.CACHE_LOCAL_ENABLED:
                local_value = local_cache_manager.get(cache_key)
                if local_value is not None:
                    return local_value

            # L2: Redis cache
            try:
                redis_value = await redis_client.get(cache_key)
                if redis_value is not None:
                    result = _deserialize_result(redis_value)
                    # Populate L1
                    if settings.CACHE_LOCAL_ENABLED:
                        local_cache_manager.set(cache_key, result)
                    return result
            except Exception as e:
                log.warning(f'[Cache] GET error: {e}')

            # Cache miss
            result = await func(*args, **kwargs)

            if result is not None:
                try:
                    serialized_result = _serialize_result(result)
                    deserialized_result = _deserialize_result(serialized_result)

                    # Populate L1
                    if settings.CACHE_LOCAL_ENABLED:
                        local_cache_manager.set(cache_key, deserialized_result)

                    # Populate L2
                    if settings.CACHE_REDIS_TTL:
                        await redis_client.set(cache_key, serialized_result, ex=settings.CACHE_REDIS_TTL)
                    else:
                        await redis_client.set(cache_key, serialized_result)
                except Exception as e:
                    log.warning(f'[Cache] SET error: {e}')

            return result

        return wrapper

    return decorator


def cache_invalidate(  # ruff:ignore[complex-structure]
    namespace: str,
    *,
    key: str | None = None,
    key_builder: Callable[..., str | Awaitable[str]] | None = None,
    atomic: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Cache invalidation decorator

    :param namespace: Cache namespace (usually the cache key prefix)
    :param key: Use the named method argument as the cache key; mutually exclusive with key_builder
    :param key_builder: Custom key builder function; mutually exclusive with key
    :param atomic: Whether to guarantee atomic cache invalidation
    :return:
    """
    if key is not None and key_builder is not None:
        raise errors.ServerError(msg='key and key_builder cannot be used together')

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            result = await func(*args, **kwargs)

            # Attempt cache invalidation
            invalidate_success = False
            invalidate_error = None

            try:
                invalidate_key = await _build_cache_key(namespace, key, key_builder, *args, **kwargs)

                # Invalidate L1 cache
                if settings.CACHE_LOCAL_ENABLED:
                    if invalidate_key == namespace:
                        local_cache_manager.delete_by_prefix(invalidate_key)
                    else:
                        local_cache_manager.delete(invalidate_key)

                # Broadcast invalidation message to clear local caches on other nodes
                if settings.CACHE_LOCAL_ENABLED:
                    if invalidate_key == namespace:
                        await cache_pubsub_manager.publish_invalidation(invalidate_key, delete_by_prefix=True)
                    else:
                        await cache_pubsub_manager.publish_invalidation(invalidate_key, delete_by_prefix=False)

                # Invalidate L2 cache
                if invalidate_key == namespace:
                    await redis_client.delete_by_prefix(invalidate_key)
                else:
                    await redis_client.delete(invalidate_key)

            except Exception as e:
                log.error(f'[Cache] INVALIDATE error: {e}')
                invalidate_error = e
            else:
                invalidate_success = True

            # Atomicity check
            if atomic and not invalidate_success:
                raise errors.ServerError(
                    msg='Cache invalidation failed; data may be inconsistent', data=invalidate_error
                )

            return result

        return wrapper

    return decorator
