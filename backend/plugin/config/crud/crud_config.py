from collections.abc import Sequence

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.plugin.config.model import Config
from backend.plugin.config.schema.config import CreateConfigParam, UpdateConfigParam
from backend.utils.timezone import timezone


class CRUDConfig(CRUDPlus[Config]):
    """System configuration parameter database operations"""

    async def get(self, db: AsyncSession, pk: int) -> Config | None:
        """
        Get configuration parameter details

        :param db: Database session
        :param pk: Configuration parameter ID
        :return:
        """
        return await self.select_model_by_column(db, id=pk, deleted=0)

    async def get_all(self, db: AsyncSession, type: str | None) -> Sequence[Config | None]:
        """
        Get configuration parameter by key

        :param db: Database session
        :param type: Configuration parameter type
        :return:
        """
        filters = {'deleted': 0}

        if type is not None:
            filters['type'] = type

        return await self.select_models(db, **filters)

    async def get_all_by_ids(self, db: AsyncSession, pks: list[int]) -> Sequence[Config]:
        """
        Get configuration parameters in bulk by ID list

        :param db: Database session
        :param pks: Configuration parameter ID list
        :return:
        """
        return await self.select_models(db, id__in=pks, deleted=0)

    async def get_all_by_keys(self, db: AsyncSession, keys: list[str]) -> Sequence[Config]:
        """
        Get configuration parameters in bulk by key list

        :param db: Database session
        :param keys: Configuration parameter key list
        :return:
        """
        return await self.select_models(db, key__in=keys, deleted=0)

    async def get_by_key(self, db: AsyncSession, key: str) -> Config | None:
        """
        Get configuration parameter by key

        :param db: Database session
        :param key: Configuration parameter key
        :return:
        """
        return await self.select_model_by_column(db, key=key, deleted=0)

    async def get_select(self, name: str | None, type: str | None) -> Select:
        """
        Get the query expression for the configuration parameter list

        :param name: Configuration parameter name
        :param type: Configuration parameter type
        :return:
        """
        filters = {'deleted': 0}

        if name is not None:
            filters['name__like'] = f'%{name}%'
        if type is not None:
            filters['type__like'] = f'%{type}%'

        return await self.select_order('created_time', 'desc', **filters)

    async def create(self, db: AsyncSession, obj: CreateConfigParam) -> None:
        """
        Create configuration parameter

        :param db: Database session
        :param obj: Configuration parameter creation parameters
        :return:
        """
        await self.create_model(db, obj)

    async def update(self, db: AsyncSession, pk: int, obj: UpdateConfigParam) -> int:
        """
        Update configuration parameter

        :param db: Database session
        :param pk: Configuration parameter ID
        :param obj: Configuration parameter update parameters
        :return:
        """
        return await self.update_model_by_column(db, obj, id=pk, deleted=0)

    async def bulk_update(self, db: AsyncSession, objs: list[UpdateConfigParam]) -> int:
        """
        Update configuration parameters in bulk

        :param db: Database session
        :param objs: Bulk configuration parameter update parameters
        :return:
        """
        return await self.bulk_update_models(db, objs)

    async def delete(self, db: AsyncSession, pks: list[int]) -> int:
        """
        Delete configuration parameters in bulk

        :param db: Database session
        :param pks: Configuration parameter ID list
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


config_dao: CRUDConfig = CRUDConfig(Config)
