from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic_core import from_json
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.authentication import UnauthenticatedUser

from backend.app.admin.model import User
from backend.app.admin.schema.user import GetUserInfoWithRelationDetail
from backend.common.context import ctx
from backend.common.dataclasses import TokenPayload
from backend.common.exception import errors
from backend.core.conf import settings
from backend.database.db import async_db_session
from backend.database.redis import redis_client
from backend.utils.timezone import timezone


def jwt_encode(payload: dict[str, Any]) -> str:
    """
    Generate JWT token

    :param payload: Payload
    :return:
    """
    return jwt.encode(payload, settings.TOKEN_SECRET_KEY, settings.TOKEN_ALGORITHM)


def jwt_decode(token: str) -> TokenPayload:
    """
    Parse JWT token

    :param token: JWT token
    :return:
    """
    try:
        payload = jwt.decode(
            token,
            settings.TOKEN_SECRET_KEY,
            algorithms=[settings.TOKEN_ALGORITHM],
            options={'verify_exp': True},
        )
        session_uuid = payload.get('session_uuid')
        user_id = payload.get('sub')
        expire = payload.get('exp')
        if not session_uuid or not user_id or not expire:
            raise errors.TokenError(msg='Invalid token')
    except ExpiredSignatureError:
        raise errors.TokenError(msg='Token has expired')
    except (JWTError, Exception):
        raise errors.TokenError(msg='Invalid token')
    return TokenPayload(
        user_id=int(user_id),
        session_uuid=session_uuid,
        expire_time=timezone.from_datetime(timezone.to_utc(expire)),
    )


async def get_current_user(db: AsyncSession, pk: int) -> User:
    """
    Get current user

    :param db: Database session
    :param pk: User ID
    :return:
    """
    from backend.app.admin.crud.crud_user import user_dao

    user = await user_dao.get_join(db, user_id=pk)
    if not user:
        raise errors.TokenError(msg='Invalid token')
    if not user.status:
        raise errors.AuthorizationError(msg='User is locked; contact the system administrator')
    if user.dept_id and not user.dept:
        raise errors.AuthorizationError(
            msg='User department does not exist or has been deleted; contact the system administrator'
        )
    if user.dept and not user.dept.status:
        raise errors.AuthorizationError(msg='User department is locked; contact the system administrator')
    if user.roles:
        role_status = [role.status for role in user.roles]
        if all(status == 0 for status in role_status):
            raise errors.AuthorizationError(msg='User role is locked; contact the system administrator')
    return user


async def get_jwt_user(user_id: int) -> GetUserInfoWithRelationDetail:
    """
    Get JWT user

    :param user_id: User ID
    :return:
    """
    user_key = f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}'
    cache_user = await redis_client.get(user_key)
    if not cache_user:
        async with async_db_session() as db:
            current_user = await get_current_user(db, user_id)
            user = GetUserInfoWithRelationDetail.model_validate(current_user)
            await redis_client.set(
                user_key,
                user.model_dump_json(),
                ex=settings.TOKEN_EXPIRE_SECONDS,
            )
    else:
        # TODO: Replace with model_validate_json when appropriate
        # https://docs.pydantic.dev/latest/concepts/json/#partial-json-parsing
        user = GetUserInfoWithRelationDetail.model_validate(from_json(cache_user, allow_partial=True))
    return user


async def jwt_authentication(token: str) -> GetUserInfoWithRelationDetail:
    """
    JWT authentication

    :param token: JWT token
    :return:
    """
    token_payload = jwt_decode(token)
    ctx.user_id = token_payload.user_id
    redis_token = await redis_client.get(f'{settings.TOKEN_REDIS_PREFIX}:{ctx.user_id}:{token_payload.session_uuid}')
    if not redis_token:
        raise errors.TokenError(msg='Token has expired')
    if token != redis_token:
        raise errors.TokenError(msg='Token is no longer valid')

    user = await get_jwt_user(ctx.user_id)
    ctx.is_superuser = user.is_superuser
    return user


def jwt_authentication_verify(
    request: Request,
    token: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
) -> str:
    """
    JWT authentication dependency

    :param request: FastAPI request object
    :param token: HTTP Bearer authentication credentials
    :return:
    """
    if isinstance(request.user, UnauthenticatedUser):
        if token_exception := ctx.get('__request_jwt_authentication_exception__'):
            raise token_exception
        raise errors.TokenError
    return token.credentials


# JWT dependency injection
DependsJwtAuth = Depends(jwt_authentication_verify)


def superuser_verify(request: Request, _token: str = DependsJwtAuth) -> bool:
    """
    Verify that the current user has superuser privileges

    :param request: FastAPI request object
    :param _token: JWT token
    :return:
    """
    if isinstance(request.user, UnauthenticatedUser):
        raise errors.TokenError
    superuser = request.user.is_superuser
    if not superuser or not request.user.is_staff:
        raise errors.AuthorizationError
    return superuser


# Superuser authorization dependency injection
DependsSuperUser = Depends(superuser_verify)
