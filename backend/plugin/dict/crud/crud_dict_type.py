from collections.abc import Sequence

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.plugin.dict.crud.crud_dict_data import dict_data_dao
from backend.plugin.dict.model import DictType
from backend.plugin.dict.schema.dict_type import CreateDictTypeParam, UpdateDictTypeParam
from backend.utils.timezone import timezone


class CRUDDictType(CRUDPlus[DictType]):
    """Dictionary type database operations"""

    async def get(self, db: AsyncSession, pk: int) -> DictType | None:
        """
        Get dictionary type details

        :param db: Database session
        :param pk: Dictionary type ID
        :return:
        """
        return await self.select_model(db, pk, deleted=0)

    async def get_all(self, db: AsyncSession) -> Sequence[DictType]:
        """
        Get all dictionary types

        :param db: Database session
        :return:
        """
        return await self.select_models(db, deleted=0)

    async def get_select(self, name: str | None, code: str | None) -> Select:
        """
        Get the query expression for the dictionary type list

        :param name: Dictionary type name
        :param code: Dictionary type code
        :return:
        """
        filters = {'deleted': 0}

        if name is not None:
            filters['name__like'] = f'%{name}%'
        if code is not None:
            filters['code__like'] = f'%{code}%'

        return await self.select_order('id', 'desc', **filters)

    async def get_by_code(self, db: AsyncSession, code: str) -> DictType | None:
        """
        Get dictionary type by code

        :param db: Database session
        :param code: Dictionary code
        :return:
        """
        return await self.select_model_by_column(db, code=code, deleted=0)

    async def create(self, db: AsyncSession, obj: CreateDictTypeParam) -> None:
        """
        Create dictionary type

        :param db: Database session
        :param obj: Dictionary type creation parameters
        :return:
        """
        await self.create_model(db, obj)

    async def update(self, db: AsyncSession, pk: int, obj: UpdateDictTypeParam) -> int:
        """
        Update dictionary type

        :param db: Database session
        :param pk: Dictionary type ID
        :param obj: Dictionary type update parameters
        :return:
        """
        return await self.update_model_by_column(db, obj, id=pk, deleted=0)

    async def delete(self, db: AsyncSession, pks: list[int]) -> int:
        """
        Delete dictionary types in bulk

        :param db: Database session
        :param pks: Dictionary type ID list
        :return:
        """
        await dict_data_dao.delete_by_type_id(db, pks)
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


dict_type_dao: CRUDDictType = CRUDDictType(DictType)
