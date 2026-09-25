from fastapi import Request, Response
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask, BackgroundTasks

from backend.app.admin.crud.crud_menu import menu_dao
from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model import User
from backend.app.admin.schema.token import GetLoginToken, GetNewToken
from backend.app.admin.schema.user import AuthLoginParam
from backend.app.admin.service.login_log_service import login_log_service
from backend.app.admin.service.user_password_history_service import password_security_service
from backend.app.admin.utils.password_security import password_verify
from backend.common.context import ctx
from backend.common.enums import LoginLogStatusType, StatusType
from backend.common.exception import errors
from backend.common.i18n import t
from backend.common.log import log
from backend.common.response.response_code import CustomErrorCode
from backend.common.security.jwt import jwt_decode
from backend.common.security.token import (
    create_access_token,
    create_new_token,
    create_refresh_token,
    get_token,
    get_user_sessions,
    revoke_token,
)
from backend.core.conf import settings
from backend.database.db import uuid4_str
from backend.database.redis import redis_client
from backend.utils.dynamic_config import load_login_config
from backend.utils.timezone import timezone


class AuthService:
    """Authentication service"""

    @staticmethod
    async def user_verify(*, db: AsyncSession, username: str, password: str) -> tuple[User, int | None]:
        """
        Validate username and password

        :param db: Database session
        :param username: Username
        :param password: Password
        :return:
        """
        user = await user_dao.get_by_username(db, username)
        if not user:
            raise errors.NotFoundError(msg='Incorrect username or password')
        await password_security_service.check_status(user.id, user.status)
        if user.password is None or not password_verify(password, user.password):
            await password_security_service.handle_login_failure(db, user.id)
            raise errors.AuthorizationError(msg='Incorrect username or password')

        days_remaining = await password_security_service.check_password_expiry_status(
            db, user.last_password_changed_time
        )
        await password_security_service.handle_login_success(user.id)

        return user, days_remaining

    async def swagger_login(self, *, db: AsyncSession, obj: HTTPBasicCredentials) -> tuple[str, User]:
        """
        Swagger documentation login

        :param db: Database session
        :param obj: Login credentials
        :return:
        """
        user, _ = await self.user_verify(db=db, username=obj.username, password=obj.password)
        await user_dao.update_login_time(db, obj.username)
        access_token_data = await create_access_token(
            user.id,
            multi_login=user.is_multi_login,
            swagger=True,
        )
        return access_token_data.access_token, user

    async def login(
        self,
        *,
        db: AsyncSession,
        response: Response,
        obj: AuthLoginParam,
        background_tasks: BackgroundTasks,
    ) -> GetLoginToken:
        """
        User login

        :param db: Database session
        :param response: Response object
        :param obj: Login parameters
        :param background_tasks: Background tasks
        :return:
        """
        user = None
        try:
            await load_login_config(db)
            if settings.LOGIN_CAPTCHA_ENABLED:
                if not obj.uuid or not obj.captcha:
                    raise errors.RequestError(msg=t('error.captcha.invalid'))
                captcha_key = f'{settings.LOGIN_CAPTCHA_REDIS_PREFIX}:{obj.uuid}'
                captcha_code = await redis_client.get(captcha_key)
                if not captcha_code:
                    raise errors.RequestError(msg=t('error.captcha.expired'))
                if captcha_code.lower() != obj.captcha.lower():
                    raise errors.CustomError(error=CustomErrorCode.CAPTCHA_ERROR)
                await redis_client.delete(captcha_key)

            user, days_remaining = await self.user_verify(db=db, username=obj.username, password=obj.password)
            await user_dao.update_login_time(db, obj.username)
            await db.refresh(user)
            access_token_data = await create_access_token(
                user.id,
                multi_login=user.is_multi_login,
                # extra info
                username=user.username,
                nickname=user.nickname,
                last_login_time=timezone.to_str(user.last_login_time),
                ip=ctx.ip,
                os=ctx.os,
                browser=ctx.browser,
                device=ctx.device,
            )
            refresh_token_data = await create_refresh_token(
                access_token_data.session_uuid,
                user.id,
                multi_login=user.is_multi_login,
            )
            response.set_cookie(
                key=settings.COOKIE_REFRESH_TOKEN_KEY,
                value=refresh_token_data.refresh_token,
                max_age=settings.COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS,
                expires=timezone.to_utc(refresh_token_data.refresh_token_expire_time),
                httponly=True,
            )
        except errors.NotFoundError as e:
            log.error('Login error: username does not exist')
            raise errors.NotFoundError(msg=e.msg)
        except (errors.RequestError, errors.CustomError) as e:
            if not user:
                log.error(f'Login error: {e.msg}')
            task = BackgroundTask(
                login_log_service.create,
                user_uuid=user.uuid if user else uuid4_str(),
                username=obj.username,
                login_time=timezone.now(),
                status=LoginLogStatusType.fail.value,
                msg=e.msg,
            )
            raise errors.RequestError(code=e.code, msg=e.msg, background=task)
        except Exception as e:
            log.error(f'Login error: {e}')
            raise
        else:
            background_tasks.add_task(
                login_log_service.create,
                user_uuid=user.uuid,
                username=obj.username,
                login_time=timezone.now(),
                status=LoginLogStatusType.success.value,
                msg=t('success.login.success'),
            )
            data = GetLoginToken(
                access_token=access_token_data.access_token,
                access_token_expire_time=access_token_data.access_token_expire_time,
                session_uuid=access_token_data.session_uuid,
                password_expire_days_remaining=days_remaining,
                user=user,  # type: ignore
            )
            return data

    @staticmethod
    async def get_codes(*, db: AsyncSession, request: Request) -> list[str]:
        """
        Get user permission codes

        :param db: Database session
        :param request: FastAPI request object
        :return:
        """
        codes = set()
        if request.user.is_superuser:
            menus = await menu_dao.get_all(db, None, None)
            for menu in menus:
                if menu.status == StatusType.enable and menu.perms:
                    codes.update(menu.perms.split(','))
        else:
            roles = [role for role in request.user.roles if role.status == StatusType.enable]
            if roles:
                for role in roles:
                    for menu in role.menus:
                        if menu.status == StatusType.enable and menu.perms:
                            codes.update(menu.perms.split(','))

        return list(codes)

    @staticmethod
    async def refresh_token(*, db: AsyncSession, request: Request, response: Response) -> GetNewToken:
        """
        Refresh token

        :param db: Database session
        :param request: FastAPI request object
        :param response: FastAPI response object
        :return:
        """
        refresh_token = request.cookies.get(settings.COOKIE_REFRESH_TOKEN_KEY)
        if not refresh_token:
            raise errors.RequestError(msg='Refresh token has expired; please log in again')

        token_payload = jwt_decode(refresh_token)
        user = await user_dao.get(db, token_payload.user_id)
        if not user:
            raise errors.NotFoundError(msg='User does not exist')
        if not user.status:
            raise errors.AuthorizationError(msg='User is locked; contact the system administrator')
        if not user.is_multi_login and await get_user_sessions(user.id) - {token_payload.session_uuid}:
            raise errors.ForbiddenError(
                msg='This user has logged in elsewhere; please log in again and change your password promptly'
            )

        new_token = await create_new_token(
            refresh_token,
            token_payload.session_uuid,
            user.id,
            multi_login=user.is_multi_login,
            # extra info
            username=user.username,
            nickname=user.nickname,
            last_login_time=timezone.to_str(user.last_login_time),
            ip=ctx.ip,
            os=ctx.os,
            browser=ctx.browser,
            device_type=ctx.device,
        )
        response.set_cookie(
            key=settings.COOKIE_REFRESH_TOKEN_KEY,
            value=new_token.new_refresh_token,
            max_age=settings.COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS,
            expires=timezone.to_utc(new_token.new_refresh_token_expire_time),
            httponly=True,
        )

        data = GetNewToken(
            access_token=new_token.new_access_token,
            access_token_expire_time=new_token.new_access_token_expire_time,
            session_uuid=new_token.session_uuid,
        )
        return data

    @staticmethod
    async def logout(*, request: Request, response: Response) -> None:
        """
        User logout

        :param request: FastAPI request object
        :param response: FastAPI response object
        :return:
        """
        try:
            token = get_token(request)
            token_payload = jwt_decode(token)
        except errors.TokenError:
            return
        finally:
            response.delete_cookie(settings.COOKIE_REFRESH_TOKEN_KEY)

        await revoke_token(token_payload.user_id, token_payload.session_uuid)


auth_service: AuthService = AuthService()
