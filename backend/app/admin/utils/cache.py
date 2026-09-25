from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import data_scope_rule, role_data_scope, role_menu, user_role
from backend.core.conf import settings
from backend.database.redis import redis_client


class UserCacheManager:
    """User cache management"""

    @staticmethod
    async def clear(user_ids: Sequence[int]) -> None:
        """
        Clear user cache

        :param user_ids: User ID list
        :return:
        """
        if user_ids:
            await redis_client.delete(*[f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}' for user_id in user_ids])

    async def clear_by_role_id(self, db: AsyncSession, role_ids: list[int]) -> None:
        """
        Clear user cache by role ID

        :param db: Database session
        :param role_ids: Role ID list
        :return:
        """
        stmt = select(user_role.c.user_id).where(user_role.c.role_id.in_(role_ids)).distinct()
        result = await db.execute(stmt)
        user_ids = result.scalars().all()

        await self.clear(user_ids)

    async def clear_by_menu_id(self, db: AsyncSession, menu_ids: list[int]) -> None:
        """
        Clear user cache by menu ID

        :param db: Database session
        :param menu_ids: Menu ID list
        :return:
        """
        stmt = (
            select(user_role.c.user_id)
            .join(role_menu, user_role.c.role_id == role_menu.c.role_id)
            .where(role_menu.c.menu_id.in_(menu_ids))
            .distinct()
        )
        result = await db.execute(stmt)
        user_ids = result.scalars().all()

        await self.clear(user_ids)

    async def clear_by_data_scope_id(self, db: AsyncSession, scope_ids: list[int]) -> None:
        """
        Clear user cache by data scope ID

        :param db: Database session
        :param scope_ids: Data scope ID list
        :return:
        """
        stmt = (
            select(user_role.c.user_id)
            .join(role_data_scope, user_role.c.role_id == role_data_scope.c.role_id)
            .where(role_data_scope.c.data_scope_id.in_(scope_ids))
            .distinct()
        )
        result = await db.execute(stmt)
        user_ids = result.scalars().all()

        await self.clear(user_ids)

    async def clear_by_data_rule_id(self, db: AsyncSession, rule_ids: list[int]) -> None:
        """
        Clear user cache by data rule ID

        :param db: Database session
        :param rule_ids: Data rule ID list
        :return:
        """
        stmt = (
            select(user_role.c.user_id)
            .join(role_data_scope, user_role.c.role_id == role_data_scope.c.role_id)
            .join(data_scope_rule, role_data_scope.c.data_scope_id == data_scope_rule.c.data_scope_id)
            .where(data_scope_rule.c.data_rule_id.in_(rule_ids))
            .distinct()
        )
        result = await db.execute(stmt)
        user_ids = result.scalars().all()

        await self.clear(user_ids)


user_cache_manager: UserCacheManager = UserCacheManager()
