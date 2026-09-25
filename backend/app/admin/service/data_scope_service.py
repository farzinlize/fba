from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_data_rule import data_rule_dao
from backend.app.admin.crud.crud_data_scope import data_scope_dao
from backend.app.admin.model import DataScope
from backend.app.admin.schema.data_scope import (
    CreateDataScopeParam,
    DeleteDataScopeParam,
    UpdateDataScopeParam,
    UpdateDataScopeRuleParam,
)
from backend.app.admin.utils.cache import user_cache_manager
from backend.common.exception import errors
from backend.common.pagination import paging_data


class DataScopeService:
    """Data scope service"""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> DataScope:
        """
        Get data scope details

        :param db: Database session
        :param pk: Scope ID
        :return:
        """

        data_scope = await data_scope_dao.get(db, pk)
        if not data_scope:
            raise errors.NotFoundError(msg='Data scope does not exist')
        return data_scope

    @staticmethod
    async def get_all(*, db: AsyncSession) -> Sequence[DataScope]:
        """
        Get all data scopes

        :param db: Database session
        :return:
        """

        data_scopes = await data_scope_dao.get_all(db)
        return data_scopes

    @staticmethod
    async def get_rules(*, db: AsyncSession, pk: int) -> DataScope:
        """
        Get data scope rules

        :param db: Database session
        :param pk: Scope ID
        :return:
        """

        data_scope = await data_scope_dao.get_join(db, pk)
        if not data_scope:
            raise errors.NotFoundError(msg='Data scope does not exist')
        return data_scope

    @staticmethod
    async def get_list(*, db: AsyncSession, name: str | None, status: int | None) -> dict[str, Any]:
        """
        Get data scope list

        :param db: Database session
        :param name: Scope name
        :param status: Scope status
        :return:
        """
        data_scope_select = await data_scope_dao.get_select(name, status)
        return await paging_data(db, data_scope_select)

    @staticmethod
    async def create(*, db: AsyncSession, obj: CreateDataScopeParam) -> None:
        """
        Create data scope

        :param db: Database session
        :param obj: Data scope parameters
        :return:
        """
        data_scope = await data_scope_dao.get_by_name(db, obj.name)
        if data_scope:
            raise errors.ConflictError(msg='Data scope already exists')
        await data_scope_dao.create(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateDataScopeParam) -> int:
        """
        Update data scope

        :param db: Database session
        :param pk: Scope ID
        :param obj: Data scope update parameters
        :return:
        """
        data_scope = await data_scope_dao.get(db, pk)
        if not data_scope:
            raise errors.NotFoundError(msg='Data scope does not exist')
        if data_scope.name != obj.name and await data_scope_dao.get_by_name(db, obj.name):
            raise errors.ConflictError(msg='Data scope already exists')
        count = await data_scope_dao.update(db, pk, obj)
        await user_cache_manager.clear_by_data_scope_id(db, [pk])
        return count

    @staticmethod
    async def update_data_scope_rule(*, db: AsyncSession, pk: int, rule_ids: UpdateDataScopeRuleParam) -> int:
        """
        Update data scope rules

        :param db: Database session
        :param pk: Scope ID
        :param rule_ids: Rule ID list
        :return:
        """
        data_scope = await data_scope_dao.get(db, pk)
        if not data_scope:
            raise errors.NotFoundError(msg='Data scope does not exist')
        if rule_ids.rules:
            rules = await data_rule_dao.get_all_by_ids(db, list(set(rule_ids.rules)))
            if {rule.id for rule in rules} != set(rule_ids.rules):
                raise errors.NotFoundError(msg='Data rule does not exist')
        count = await data_scope_dao.update_rules(db, pk, rule_ids)
        await user_cache_manager.clear_by_data_scope_id(db, [pk])
        return count

    @staticmethod
    async def delete(*, db: AsyncSession, obj: DeleteDataScopeParam) -> int:
        """
        Delete data scopes in bulk

        :param db: Database session
        :param obj: Scope ID list
        :return:
        """
        count = await data_scope_dao.delete(db, obj.pks)
        await user_cache_manager.clear_by_data_scope_id(db, obj.pks)
        return count


data_scope_service: DataScopeService = DataScopeService()
