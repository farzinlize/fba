from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_menu import menu_dao
from backend.app.admin.model import Menu
from backend.app.admin.schema.menu import CreateMenuParam, UpdateMenuParam
from backend.app.admin.utils.cache import user_cache_manager
from backend.common.enums import StatusType
from backend.common.exception import errors
from backend.utils.build_tree import get_tree_data, get_vben5_tree_data


class MenuService:
    """Menu service"""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> Menu:
        """
        Get menu details

        :param db: Database session
        :param pk: Menu ID
        :return:
        """

        menu = await menu_dao.get(db, menu_id=pk)
        if not menu:
            raise errors.NotFoundError(msg='Menu does not exist')
        return menu

    @staticmethod
    async def get_tree(*, db: AsyncSession, title: str | None, status: int | None) -> list[dict[str, Any]]:
        """
        Get menu tree structure

        :param db: Database session
        :param title: Menu title
        :param status: Status
        :return:
        """

        menu_data = await menu_dao.get_all(db, title=title, status=status)
        menu_tree = get_tree_data(menu_data)
        return menu_tree

    @staticmethod
    async def get_sidebar(*, db: AsyncSession, request: Request) -> list[dict[str, Any] | None]:
        """
        Get user sidebar menus

        :param db: Database session
        :param request: FastAPI request object
        :return:
        """
        menu_data = None
        if request.user.is_superuser:
            menu_data = await menu_dao.get_sidebar(db, None)
        else:
            roles = [role for role in request.user.roles if role.status == StatusType.enable]
            menu_ids = set()
            if roles:
                for role in roles:
                    menu_ids.update(menu.id for menu in role.menus)
                menu_data = await menu_dao.get_sidebar(db, list(menu_ids))

        if menu_data:
            return get_vben5_tree_data(menu_data)

        return []

    @staticmethod
    async def create(*, db: AsyncSession, obj: CreateMenuParam) -> None:
        """
        Create menu

        :param db: Database session
        :param obj: Menu creation parameters
        :return:
        """

        title = await menu_dao.get_by_title(db, obj.title)
        if title:
            raise errors.ConflictError(msg='Menu title already exists')
        if obj.parent_id:
            parent_menu = await menu_dao.get(db, obj.parent_id)
            if not parent_menu:
                raise errors.NotFoundError(msg='Parent menu does not exist')
        await menu_dao.create(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateMenuParam) -> int:
        """
        Update menu

        :param db: Database session
        :param pk: Menu ID
        :param obj: Menu update parameters
        :return:
        """

        menu = await menu_dao.get(db, pk)
        if not menu:
            raise errors.NotFoundError(msg='Menu does not exist')
        if menu.title != obj.title and await menu_dao.get_by_title(db, obj.title):
            raise errors.ConflictError(msg='Menu title already exists')
        if obj.parent_id:
            parent_menu = await menu_dao.get(db, obj.parent_id)
            if not parent_menu:
                raise errors.NotFoundError(msg='Parent menu does not exist')
        if obj.parent_id == menu.id:
            raise errors.ForbiddenError(msg='Cannot set an item as its own parent')
        count = await menu_dao.update(db, pk, obj)
        await user_cache_manager.clear_by_menu_id(db, [pk])
        return count

    @staticmethod
    async def delete(*, db: AsyncSession, pk: int) -> int:
        """
        Delete menu

        :param db: Database session
        :param pk: Menu ID
        :return:
        """

        children = await menu_dao.get_children(db, pk)
        if children:
            raise errors.ConflictError(msg='Cannot delete a menu that contains child menus')
        count = await menu_dao.delete(db, pk)
        if count:
            await user_cache_manager.clear_by_menu_id(db, [pk])
        return count


menu_service: MenuService = MenuService()
