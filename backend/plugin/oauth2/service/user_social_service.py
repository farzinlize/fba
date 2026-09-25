import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.exception import errors
from backend.core.conf import settings
from backend.database.redis import redis_client
from backend.plugin.oauth2.crud.crud_user_social import user_social_dao
from backend.plugin.oauth2.enums import UserSocialAuthType, UserSocialType
from backend.plugin.oauth2.schema.user_social import CreateUserSocialParam


class UserSocialService:
    """User social account service"""

    @staticmethod
    async def get_bindings(*, db: AsyncSession, user_id: int) -> list[str]:
        """
        Get linked social accounts for the user

        :param db: Database session
        :param user_id: User ID
        :return:
        """
        bindings = await user_social_dao.get_by_user_id(db, user_id)
        return [binding.source for binding in bindings]

    @staticmethod
    async def binding_with_oauth2(
        *,
        db: AsyncSession,
        user_id: int,
        sid: str,
        source: UserSocialType,
    ) -> None:
        """
        Link user social account through OAuth2

        :param db: Database session
        :param user_id: User ID
        :param sid: Unique social account identifier
        :param source: Provider to link
        :return:
        """
        if await user_social_dao.check_binding(db, user_id, source.value):
            raise errors.RequestError(msg=f'User already has a linked {source.value} account')

        if await user_social_dao.get_by_sid(db, sid, source.value):
            raise errors.RequestError(msg=f'This {source.value} account is already linked to another user')

        new_user_social = CreateUserSocialParam(sid=sid, source=source.value, user_id=user_id)
        await user_social_dao.create(db, new_user_social)

    @staticmethod
    async def unbinding(*, db: AsyncSession, user_id: int, source: UserSocialType) -> int:
        """
        Unlink user social account

        :param db: Database session
        :param user_id: User ID
        :param source: Provider to unlink
        :return:
        """
        bind = await user_social_dao.check_binding(db, user_id, source.value)
        if not bind:
            raise errors.NotFoundError(msg=f'User has no linked {source.value} account')
        return await user_social_dao.delete(db, user_id, source.value)

    @staticmethod
    async def get_binding_auth_url(*, user_id: int, source: UserSocialType) -> str:
        state = str(uuid.uuid4())

        await redis_client.set(
            f'{settings.OAUTH2_STATE_REDIS_PREFIX}:{state}',
            json.dumps({'type': UserSocialAuthType.binding.value, 'user_id': user_id}),
            ex=settings.OAUTH2_STATE_EXPIRE_SECONDS,
        )

        match source:
            case UserSocialType.github:
                from backend.plugin.oauth2.api.v1.github import github_client

                auth_url = await github_client.get_authorization_url(
                    redirect_uri=settings.OAUTH2_GITHUB_REDIRECT_URI,
                    state=state,
                )
            case UserSocialType.google:
                from backend.plugin.oauth2.api.v1.google import google_client

                auth_url = await google_client.get_authorization_url(
                    redirect_uri=settings.OAUTH2_GOOGLE_REDIRECT_URI,
                    state=state,
                )
            case _:
                raise errors.ForbiddenError(msg=f'Account linking through {source} is not supported')

        return auth_url


user_social_service: UserSocialService = UserSocialService()
