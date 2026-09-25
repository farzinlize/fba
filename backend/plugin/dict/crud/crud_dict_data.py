from collections.abc import Sequence

from sqlalchemy import Select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.common.enums import StatusType
from backend.plugin.dict.model import DictData
from backend.plugin.dict.schema.dict_data import CreateDictDataParam, UpdateDictDataParam
from backend.utils.timezone import timezone


class CRUDDictData(CRUDPlus[DictData]):
    """Dictionary entry database operations"""

    async def get(self, db: AsyncSession, pk: int) -> DictData | None:
        """
        Get dictionary entry details

        :param db: Database session
        :param pk: Dictionary entry ID
        :return:
        """
        return await self.select_model(db, pk, deleted=0)

    async def get_by_type_code(self, db: AsyncSession, type_code: str) -> Sequence[DictData]:
        """
        Get dictionary entries by dictionary type code

        :param db: Database session
        :param type_code: Dictionary type code
        :return:
        """
        return await self.select_models_order(
            db,
            sort_columns='sort',
            sort_orders='desc',
            type_code=type_code,
            status=StatusType.enable.value,
            deleted=0,
        )

    async def get_all(self, db: AsyncSession) -> Sequence[DictData]:
        """
        Get all dictionary entries

        :param db: Database session
        :return:
        """
        return await self.select_models(db, deleted=0)

    async def get_select(
        self,
        type_code: str | None,
        label: str | None,
        value: str | None,
        status: int | None,
        type_id: int | None,
    ) -> Select:
        """
        Get the query expression for the dictionary entry list

        :param type_code: Dictionary type code
        :param label: Dictionary entry label
        :param value: Dictionary entry value
        :param status: Dictionary status
        :param type_id: Dictionary type ID
        :return:
        """
        filters = {'deleted': 0}

        if type_code is not None:
            filters['type_code'] = type_code
        if label is not None:
            filters['label__like'] = f'%{label}%'
        if value is not None:
            filters['value__like'] = f'%{value}%'
        if status is not None:
            filters['status'] = status
        if type_id is not None:
            filters['type_id'] = type_id

        return await self.select_order('sort', 'asc', **filters)

    async def get_by_label_and_type_code(self, db: AsyncSession, label: str, type_code: str) -> DictData | None:
        """
        Get dictionary entry by label

        :param db: Database session
        :param label: Dictionary label
        :param type_code: Dictionary type code
        :return:
        """
        return await self.select_model_by_column(
            db,
            and_(self.model.label == label, self.model.type_code == type_code),
            deleted=0,
        )

    async def create(self, db: AsyncSession, obj: CreateDictDataParam, type_code: str) -> None:
        """
        Create dictionary entry

        :param db: Database session
        :param obj: Dictionary entry creation parameters
        :param type_code: Dictionary type code
        :return:
        """
        dict_obj = obj.model_dump()
        dict_obj.update({'type_code': type_code})
        new_data = self.model(**dict_obj)
        db.add(new_data)

    async def update(self, db: AsyncSession, pk: int, obj: UpdateDictDataParam, type_code: str) -> int:
        """
        Update dictionary entry

        :param db: Database session
        :param pk: Dictionary entry ID
        :param obj: Dictionary entry update parameters
        :param type_code: Dictionary type code
        :return:
        """
        dict_obj = obj.model_dump()
        dict_obj.update({'type_code': type_code})
        return await self.update_model_by_column(db, dict_obj, id=pk, deleted=0)

    async def delete(self, db: AsyncSession, pks: list[int]) -> int:
        """
        Delete dictionary entries in bulk

        :param db: Database session
        :param pks: Dictionary entry ID list
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

    async def delete_by_type_id(self, db: AsyncSession, type_ids: list[int]) -> int:
        """
        Delete dictionary entries by type ID

        :param db: Database session
        :param type_ids: Dictionary type ID list
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
            type_id__in=type_ids,
            deleted=0,
        )


dict_data_dao: CRUDDictData = CRUDDictData(DictData)
