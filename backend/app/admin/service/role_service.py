from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_data_scope import data_scope_dao
from backend.app.admin.crud.crud_menu import menu_dao
from backend.app.admin.crud.crud_role import role_dao
from backend.app.admin.model import Role
from backend.app.admin.schema.role import (
    CreateRoleParam,
    DeleteRoleParam,
    UpdateRoleMenuParam,
    UpdateRoleParam,
    UpdateRoleScopeParam,
)
from backend.app.admin.utils.cache import user_cache_manager
from backend.common.exception import errors
from backend.common.pagination import paging_data
from backend.utils.build_tree import get_tree_data


class RoleService:
    """Role service"""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> Role:
        """
        Get role details

        :param db: Database session
        :param pk: Role ID
        :return:
        """

        role = await role_dao.get_join(db, pk)
        if not role:
            raise errors.NotFoundError(msg='Role does not exist')
        return role

    @staticmethod
    async def get_all(*, db: AsyncSession) -> Sequence[Role]:
        """
        Get all roles

        :param db: Database session
        :return:
        """

        roles = await role_dao.get_all(db)
        return roles

    @staticmethod
    async def get_list(*, db: AsyncSession, name: str | None, status: int | None) -> dict[str, Any]:
        """
        Get role list

        :param db: Database session
        :param name: Role name
        :param status: Status
        :return:
        """
        role_select = await role_dao.get_select(name=name, status=status)
        return await paging_data(db, role_select)

    @staticmethod
    async def get_menu_tree(*, db: AsyncSession, pk: int) -> list[dict[str, Any] | None]:
        """
        Get role menu tree structure

        :param db: Database session
        :param pk: Role ID
        :return:
        """

        role = await role_dao.get(db, pk)
        if not role:
            raise errors.NotFoundError(msg='Role does not exist')
        menus = await role_dao.get_menus(db, pk)
        menu_tree = get_tree_data(menus) if menus else []
        return menu_tree

    @staticmethod
    async def get_scopes(*, db: AsyncSession, pk: int) -> list[int]:
        """
        Get role data scope list

        :param db: Database session
        :param pk:
        :return:
        """

        role = await role_dao.get_join(db, pk)
        if not role:
            raise errors.NotFoundError(msg='Role does not exist')
        scope_ids = [scope.id for scope in role.scopes]
        return scope_ids

    @staticmethod
    async def create(*, db: AsyncSession, obj: CreateRoleParam) -> None:
        """
        Create role

        :param db: Database session
        :param obj: Role creation parameters
        :return:
        """

        role = await role_dao.get_by_name(db, obj.name)
        if role:
            raise errors.ConflictError(msg='Role already exists')
        await role_dao.create(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateRoleParam) -> int:
        """
        Update role

        :param db: Database session
        :param pk: Role ID
        :param obj: Role update parameters
        :return:
        """

        role = await role_dao.get(db, pk)
        if not role:
            raise errors.NotFoundError(msg='Role does not exist')
        if role.name != obj.name and await role_dao.get_by_name(db, obj.name):
            raise errors.ConflictError(msg='Role already exists')
        count = await role_dao.update(db, pk, obj)
        await user_cache_manager.clear_by_role_id(db, [pk])
        return count

    @staticmethod
    async def update_role_menu(*, db: AsyncSession, pk: int, menu_ids: UpdateRoleMenuParam) -> int:
        """
        Update role menus

        :param db: Database session
        :param pk: Role ID
        :param menu_ids: Menu ID list
        :return:
        """

        role = await role_dao.get(db, pk)
        if not role:
            raise errors.NotFoundError(msg='Role does not exist')
        if menu_ids.menus:
            menus = await menu_dao.get_all_by_ids(db, list(set(menu_ids.menus)))
            if {menu.id for menu in menus} != set(menu_ids.menus):
                raise errors.NotFoundError(msg='Menu does not exist')
        count = await role_dao.update_menus(db, pk, menu_ids)
        await user_cache_manager.clear_by_role_id(db, [pk])
        return count

    @staticmethod
    async def update_role_scope(*, db: AsyncSession, pk: int, scope_ids: UpdateRoleScopeParam) -> int:
        """
        Update role data scopes

        :param db: Database session
        :param pk: Role ID
        :param scope_ids: Permission rule ID list
        :return:
        """

        role = await role_dao.get(db, pk)
        if not role:
            raise errors.NotFoundError(msg='Role does not exist')
        if scope_ids.scopes:
            scopes = await data_scope_dao.get_all_by_ids(db, list(set(scope_ids.scopes)))
            if {scope.id for scope in scopes} != set(scope_ids.scopes):
                raise errors.NotFoundError(msg='Data scope does not exist')
        count = await role_dao.update_scopes(db, pk, scope_ids)
        await user_cache_manager.clear_by_role_id(db, [pk])
        return count

    @staticmethod
    async def delete(*, db: AsyncSession, obj: DeleteRoleParam) -> int:
        """
        Delete roles in bulk

        :param db: Database session
        :param obj: Role ID list
        :return:
        """

        count = await role_dao.delete(db, obj.pks)
        await user_cache_manager.clear_by_role_id(db, obj.pks)
        return count


role_service: RoleService = RoleService()
