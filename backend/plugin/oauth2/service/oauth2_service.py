import json

from typing import Any

from fast_captcha import text_captcha
from fastapi import BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.schema.token import GetLoginToken
from backend.app.admin.schema.user import AddOAuth2UserParam
from backend.app.admin.service.login_log_service import login_log_service
from backend.common.context import ctx
from backend.common.enums import LoginLogStatusType
from backend.common.exception import errors
from backend.common.i18n import t
from backend.common.security.token import create_access_token, create_refresh_token
from backend.core.conf import settings
from backend.database.redis import redis_client
from backend.plugin.oauth2.crud.crud_user_social import user_social_dao
from backend.plugin.oauth2.enums import UserSocialAuthType, UserSocialType
from backend.plugin.oauth2.schema.user_social import CreateUserSocialParam
from backend.plugin.oauth2.service.user_social_service import user_social_service
from backend.utils.timezone import timezone


class OAuth2Service:
    """OAuth2 authentication service"""

    @staticmethod
    async def login(
        *,
        db: AsyncSession,
        response: Response,
        background_tasks: BackgroundTasks,
        sid: str,
        source: UserSocialType,
        username: str | None = None,
        nickname: str | None = None,
        email: str | None = None,
        avatar: str | None = None,
    ) -> GetLoginToken:
        """
        OAuth2 user login

        :param db: Database session
        :param response: FastAPI response object
        :param background_tasks: FastAPI background tasks
        :param sid: Unique social account identifier
        :param source: Social platform
        :param username: Username
        :param nickname: Nickname
        :param email: Email
        :param avatar: Avatar URL
        :return:
        """
        user_social = await user_social_dao.get_by_sid(db, sid, source.value)
        if user_social:
            sys_user = await user_dao.get(db, user_social.user_id)
            # Update user avatar
            if not sys_user.avatar and avatar is not None:
                await user_dao.update_avatar(db, sys_user.id, avatar)
        else:
            sys_user = None
            # Check whether the system user already exists
            if email:
                sys_user = await user_dao.check_email(db, email)

            # Create system user
            if not sys_user:
                base_username = username or text_captcha(5)
                username_candidates = [base_username, *[f'{base_username}_{text_captcha(5)}' for _ in range(10)]]
                existing_users = await user_dao.get_all_by_usernames(db, username_candidates)
                existing_usernames = {user.username for user in existing_users}
                username = next(
                    (candidate for candidate in username_candidates if candidate not in existing_usernames),
                    None,
                )
                if username is None:
                    raise errors.ConflictError(msg='Username already exists; please try again')
                new_sys_user = AddOAuth2UserParam(
                    username=username,
                    password=None,
                    nickname=nickname,
                    email=email,
                    avatar=avatar,
                )
                await user_dao.add_by_oauth2(db, new_sys_user)
                await db.flush()
                sys_user = await user_dao.get_by_username(db, username)

            # Link social account
            new_user_social = CreateUserSocialParam(sid=sid, source=source.value, user_id=sys_user.id)
            await user_social_dao.create(db, new_user_social)

        # Create token
        access_token_data = await create_access_token(
            sys_user.id,
            multi_login=sys_user.is_multi_login,
            # extra info
            username=sys_user.username,
            nickname=sys_user.nickname,
            last_login_time=timezone.to_str(timezone.now()),
            ip=ctx.ip,
            os=ctx.os,
            browser=ctx.browser,
            device=ctx.device,
        )
        refresh_token_data = await create_refresh_token(
            access_token_data.session_uuid,
            sys_user.id,
            multi_login=sys_user.is_multi_login,
        )
        await user_dao.update_login_time(db, sys_user.username)
        await db.refresh(sys_user)
        background_tasks.add_task(
            login_log_service.create,
            user_uuid=sys_user.uuid,
            username=sys_user.username,
            login_time=timezone.now(),
            status=LoginLogStatusType.success.value,
            msg=t('success.login.oauth2_success'),
        )
        await redis_client.delete(f'{settings.LOGIN_CAPTCHA_REDIS_PREFIX}:{ctx.ip}')
        response.set_cookie(
            key=settings.COOKIE_REFRESH_TOKEN_KEY,
            value=refresh_token_data.refresh_token,
            max_age=settings.COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS,
            expires=timezone.to_utc(refresh_token_data.refresh_token_expire_time),
            httponly=True,
        )
        data = GetLoginToken(
            access_token=access_token_data.access_token,
            access_token_expire_time=access_token_data.access_token_expire_time,
            session_uuid=access_token_data.session_uuid,
            user=sys_user,  # type: ignore
        )
        return data

    async def login_or_binding(
        self,
        *,
        db: AsyncSession,
        response: Response,
        background_tasks: BackgroundTasks,
        user: dict[str, Any],
        social: UserSocialType,
        state: str | None = None,
    ) -> GetLoginToken | None:
        """
        OAuth2 login or account linking

        :param db: Database session
        :param response: FastAPI response object
        :param background_tasks: FastAPI background tasks
        :param user: OAuth2 user information
        :param social: Social platform type
        :param state: OAuth2 state parameter
        :return:
        """

        sid = user.get('uuid')
        username = user.get('username')
        nickname = user.get('nickname')
        email = user.get('email')
        avatar = user.get('avatar_url')

        match social:
            case UserSocialType.github:
                sid = user.get('id')
                username = user.get('login')
                nickname = user.get('name')
            case UserSocialType.google:
                sid = user.get('id')
                username = user.get('name')
                nickname = user.get('given_name')
                avatar = user.get('picture')
            case _:
                raise errors.ForbiddenError(msg=f'OAuth2 login through {social} is not supported')

        if not state:
            raise errors.ForbiddenError(msg='OAuth2 state information is missing')

        state_data = await redis_client.get(f'{settings.OAUTH2_STATE_REDIS_PREFIX}:{state}')
        if not state_data:
            raise errors.ForbiddenError(msg='OAuth2 state information is invalid or missing')

        state_info = json.loads(state_data)
        await redis_client.delete(f'{settings.OAUTH2_STATE_REDIS_PREFIX}:{state}')

        # Account linking flow
        if state_info.get('type') == UserSocialAuthType.binding.value:
            user_id = state_info.get('user_id')
            if not user_id:
                raise errors.ForbiddenError(msg='Invalid operation: invalid OAuth2 state information')
            await user_social_service.binding_with_oauth2(
                db=db,
                user_id=user_id,
                sid=str(sid),
                source=social,
            )
            return None

        # Login flow
        if state_info.get('type') != UserSocialAuthType.login.value:
            raise errors.ForbiddenError(msg='Invalid OAuth2 state information')

        return await self.login(
            db=db,
            response=response,
            background_tasks=background_tasks,
            sid=str(sid),
            source=social,
            username=username,
            nickname=nickname,
            email=email,
            avatar=avatar,
        )


oauth2_service: OAuth2Service = OAuth2Service()
