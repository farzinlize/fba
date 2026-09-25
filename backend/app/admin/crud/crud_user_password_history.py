from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.user_password_history import UserPasswordHistory
from backend.app.admin.schema.user_password_history import CreateUserPasswordHistoryParam


class CRUDUserPasswordHistory(CRUDPlus[UserPasswordHistory]):
    """User password history database operations"""

    async def create(self, db: AsyncSession, obj: CreateUserPasswordHistoryParam) -> None:
        """
        Create password history record

        :param db: Database session
        :param obj: Password history creation parameters
        :return:
        """
        await self.create_model(db, obj)

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Sequence[UserPasswordHistory]:
        """
        Get user password history

        :param db: Database session
        :param user_id: User ID
        :return:
        """
        return await self.select_models_order(db, 'id', 'desc', self.model.user_id == user_id)


user_password_history_dao: CRUDUserPasswordHistory = CRUDUserPasswordHistory(UserPasswordHistory)
