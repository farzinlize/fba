from collections.abc import Sequence

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model import Menu, role_menu
from backend.app.admin.schema.menu import CreateMenuParam, UpdateMenuParam
from backend.utils.timezone import timezone


class CRUDMenu(CRUDPlus[Menu]):
    """Menu database operations"""

    async def get(self, db: AsyncSession, menu_id: int) -> Menu | None:
        """
        Get menu details

        :param db: Database session
        :param menu_id: Menu ID
        :return:
        """
        return await self.select_model(db, menu_id, deleted=0)

    async def get_by_title(self, db: AsyncSession, title: str) -> Menu | None:
        """
        Get menu by title

        :param db: Database session
        :param title: Menu title
        :return:
        """
        return await self.select_model_by_column(db, title=title, type__ne=2, deleted=0)

    async def get_all(self, db: AsyncSession, title: str | None, status: int | None) -> Sequence[Menu]:
        """
        Get menu list

        :param db: Database session
        :param title: Menu title
        :param status: Menu status
        :return:
        """
        filters = {'deleted': 0}

        if title is not None:
            filters['title__like'] = f'%{title}%'
        if status is not None:
            filters['status'] = status

        return await self.select_models_order(db, 'sort', 'asc', **filters)

    async def get_sidebar(self, db: AsyncSession, menu_ids: list[int] | None) -> Sequence[Menu]:
        """
        Get user sidebar menus

        :param db: Database session
        :param menu_ids: Menu ID list
        :return:
        """
        filters = {'type__in': [0, 1, 3, 4], 'deleted': 0}

        if menu_ids:
            filters['id__in'] = menu_ids

        return await self.select_models_order(db, 'sort', 'asc', **filters)

    async def get_all_by_ids(self, db: AsyncSession, menu_ids: list[int]) -> Sequence[Menu]:
        """
        Get menus in bulk by ID list

        :param db: Database session
        :param menu_ids: Menu ID list
        :return:
        """
        return await self.select_models(db, id__in=menu_ids, deleted=0)

    async def create(self, db: AsyncSession, obj: CreateMenuParam) -> None:
        """
        Create menu

        :param db: Database session
        :param obj: Menu creation parameters
        :return:
        """
        await self.create_model(db, obj)

    async def update(self, db: AsyncSession, menu_id: int, obj: UpdateMenuParam) -> int:
        """
        Update menu

        :param db: Database session
        :param menu_id: Menu ID
        :param obj: Menu update parameters
        :return:
        """
        return await self.update_model_by_column(db, obj, id=menu_id, deleted=0)

    async def delete(self, db: AsyncSession, menu_id: int) -> int:
        """
        Delete menu

        :param db: Database session
        :param menu_id: Menu ID
        :return:
        """
        role_menu_stmt = delete(role_menu).where(role_menu.c.menu_id == menu_id)
        await db.execute(role_menu_stmt)

        return await self.delete_model_by_column(
            db,
            logical_deletion=True,
            deleted_flag_column='deleted',
            deleted_flag_value=self.model.id,
            deleted_at_column='deleted_time',
            deleted_at_factory=timezone.now(),
            id=menu_id,
            deleted=0,
        )

    async def get_children(self, db: AsyncSession, menu_id: int) -> Sequence[Menu | None]:
        """
        Get child menus

        :param db: Database session
        :param menu_id: Menu ID
        :return:
        """
        return await self.select_models(db, parent_id=menu_id, deleted=0)


menu_dao: CRUDMenu = CRUDMenu(Menu)
