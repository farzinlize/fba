from collections.abc import Sequence

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model import DataRule
from backend.app.admin.schema.data_rule import CreateDataRuleParam, UpdateDataRuleParam
from backend.utils.timezone import timezone


class CRUDDataRule(CRUDPlus[DataRule]):
    """Data rule database operations"""

    async def get(self, db: AsyncSession, pk: int) -> DataRule | None:
        """
        Get rule details

        :param db: Database session
        :param pk: Rule ID
        :return:
        """
        return await self.select_model(db, pk, deleted=0)

    async def get_select(self, name: str | None) -> Select:
        """
        Get the query expression for the rule list

        :param name: Rule name
        :return:
        """
        filters = {'deleted': 0}

        if name is not None:
            filters['name__like'] = f'%{name}%'

        return await self.select_order('id', **filters)

    async def get_by_name(self, db: AsyncSession, name: str) -> DataRule | None:
        """
        Get rule by name

        :param db: Database session
        :param name: Rule name
        :return:
        """
        return await self.select_model_by_column(db, name=name, deleted=0)

    async def get_all(self, db: AsyncSession) -> Sequence[DataRule]:
        """
        Get all rules

        :param db: Database session
        :return:
        """
        return await self.select_models(db, deleted=0)

    async def get_all_by_ids(self, db: AsyncSession, pks: list[int]) -> Sequence[DataRule]:
        """
        Get data rules in bulk by ID list

        :param db: Database session
        :param pks: Rule ID list
        :return:
        """
        return await self.select_models(db, id__in=pks, deleted=0)

    async def create(self, db: AsyncSession, obj: CreateDataRuleParam) -> None:
        """
        Create rule

        :param db: Database session
        :param obj: Rule creation parameters
        :return:
        """
        await self.create_model(db, obj)

    async def update(self, db: AsyncSession, pk: int, obj: UpdateDataRuleParam) -> int:
        """
        Update rule

        :param db: Database session
        :param pk: Rule ID
        :param obj: Rule update parameters
        :return:
        """
        return await self.update_model_by_column(db, obj, id=pk, deleted=0)

    async def delete(self, db: AsyncSession, pks: list[int]) -> int:
        """
        Delete rules in bulk

        :param db: Database session
        :param pks: Rule ID list
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
            id__in=pks,
            deleted=0,
        )


data_rule_dao: CRUDDataRule = CRUDDataRule(DataRule)
