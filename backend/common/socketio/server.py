import urllib.parse
import uuid

from typing import Any

import socketio

from starlette_context import request_cycle_context

from backend.common.log import log
from backend.common.security.jwt import jwt_authentication, jwt_decode
from backend.core.conf import settings
from backend.database.redis import redis_client
from backend.utils.timezone import timezone

# Create Socket.IO server instance
sio = socketio.AsyncServer(
    client_manager=socketio.AsyncRedisManager(
        f'redis://:{urllib.parse.quote(settings.REDIS_PASSWORD)}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DATABASE}',
        redis_options={
            'socket_timeout': None,
            'socket_connect_timeout': settings.REDIS_TIMEOUT,
        },
    ),
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS,
    cors_credentials=True,
    namespaces=['/', '/ws'],
)


@sio.event(namespace='*')
async def connect(namespace: str, sid: str, _environ: dict[str, Any], auth: dict[str, Any] | None) -> bool:
    """
    Socket connection event

    :param namespace: Namespace
    :param sid: Connection ID
    :param _environ: Connection environment
    :param auth: Authentication information
    :return:
    """
    if namespace not in sio.namespaces:
        return False
    if not isinstance(auth, dict):
        log.error('WebSocket connection failed: no authentication provided')
        return False
    session_uuid = auth.get('session_uuid')
    token = auth.get('token')
    if not isinstance(token, str) or not token or not isinstance(session_uuid, str) or not session_uuid:
        log.error('WebSocket connection failed: authentication failed; check credentials')
        return False

    # Connect without authentication
    if token == settings.WS_NO_AUTH_MARKER:
        if settings.ENVIRONMENT == 'prod':
            log.error('WebSocket connection failed: unauthenticated connections are forbidden in production')
            return False
        expire = settings.TOKEN_EXPIRE_SECONDS
    else:
        try:
            with request_cycle_context({settings.TRACE_ID_REQUEST_HEADER_KEY: uuid.uuid4().hex}):
                await jwt_authentication(token)
            token_payload = jwt_decode(token)
        except Exception as e:
            log.info(f'WebSocket connection failed: {e!s}')
            return False
        session_uuid = token_payload.session_uuid
        expire = int((token_payload.expire_time - timezone.now()).total_seconds())
        if expire <= 0:
            log.info('WebSocket connection failed: token has expired')
            return False

    await sio.save_session(sid, {'session_uuid': session_uuid}, namespace=namespace)
    sid_key = f'{settings.TOKEN_ONLINE_REDIS_PREFIX}:sid:{sid}'
    session_key = f'{settings.TOKEN_ONLINE_REDIS_PREFIX}:session:{session_uuid}'
    await redis_client.set(sid_key, session_uuid, ex=expire)
    await redis_client.sadd(session_key, sid)
    session_ttl = await redis_client.ttl(session_key)
    # Set TTL from this connection for new sets; retain the longest remaining lifetime across connections
    new_ttl = expire if session_ttl < 0 else max(session_ttl, expire)
    await redis_client.expire(session_key, new_ttl)
    return True


@sio.event(namespace='*')
async def disconnect(namespace: str, sid: str, _reason: str | None = None) -> None:
    """
    Socket disconnection event

    :param namespace: Namespace
    :param sid: Connection ID
    :param _reason: Disconnection reason
    :return:
    """
    sid_key = f'{settings.TOKEN_ONLINE_REDIS_PREFIX}:sid:{sid}'
    session_uuid = await redis_client.get(sid_key)
    if not session_uuid:
        try:
            session_data = await sio.get_session(sid, namespace=namespace)
        except KeyError:
            return
        session_uuid = session_data.get('session_uuid')
    if not session_uuid:
        return

    session_key = f'{settings.TOKEN_ONLINE_REDIS_PREFIX}:session:{session_uuid}'
    await redis_client.delete(sid_key)
    await redis_client.srem(session_key, sid)
    remaining = list(await redis_client.smembers(session_key))
    if not remaining:
        return
    mappings = await redis_client.mget_batched([
        f'{settings.TOKEN_ONLINE_REDIS_PREFIX}:sid:{other_sid}' for other_sid in remaining
    ])
    stale_sids = [other_sid for other_sid, mapping in zip(remaining, mappings, strict=True) if mapping != session_uuid]
    if stale_sids:
        await redis_client.srem(session_key, *stale_sids)
