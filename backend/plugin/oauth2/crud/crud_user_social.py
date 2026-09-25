from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.plugin.oauth2.model import UserSocial
from backend.plugin.oauth2.schema.user_social import CreateUserSocialParam
from backend.utils.timezone import timezone


class CRUDUserSocial(CRUDPlus[UserSocial]):
    """User social account database operations"""

    async def check_binding(self, db: AsyncSession, user_id: int, source: str) -> UserSocial | None:
        """
        Check system user social account association

        :param db: Database session
        :param user_id: User ID
        :param source: Social account type
        :return:
        """
        return await self.select_model_by_column(db, user_id=user_id, source=source, deleted=0)

    async def get_by_sid(self, db: AsyncSession, sid: str, source: str) -> UserSocial | None:
        """
        Get social user by sid

        :param db: Database session
        :param sid: Unique social account identifier
        :param source: Social account type
        :return:
        """
        return await self.select_model_by_column(db, sid=sid, source=source, deleted=0)

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Sequence[UserSocial]:
        """
        Get all social account associations by user ID

        :param db: Database session
        :param user_id: User ID
        :return:
        """
        return await self.select_models(db, user_id=user_id, deleted=0)

    async def create(self, db: AsyncSession, obj: CreateUserSocialParam) -> None:
        """
        Create user social account association

        :param db: Database session
        :param obj: User social account association creation parameters
        :return:
        """
        await self.create_model(db, obj)

    async def delete(self, db: AsyncSession, user_id: int, source: str) -> int:
        """
        Delete user social account association

        :param db: Database session
        :param user_id: User ID
        :param source: Social account type
        :return:
        """
        return await self.delete_model_by_column(
            db,
            logical_deletion=True,
            deleted_flag_column='deleted',
            deleted_flag_value=self.model.id,
            deleted_at_column='deleted_time',
            deleted_at_factory=timezone.now(),
            user_id=user_id,
            source=source,
            deleted=0,
        )

    async def delete_by_user_id(self, db: AsyncSession, user_id: int) -> int:
        """
        Delete social accounts by user ID

        :param db: Database session
        :param user_id: User ID
        :return:
        """
        return await self.delete_model_by_column(
            db,
            allow_multiple=True,
            logical_deletion=True,
            deleted_flag_column='deleted',
            deleted_flag_value=self.model.id,
            deleted_at_column='deleted_time',
            deleted_at_factory=timezone.now(),
            user_id=user_id,
            deleted=0,
        )


user_social_dao: CRUDUserSocial = CRUDUserSocial(UserSocial)
