from collections.abc import Sequence

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.plugin.code_generator.model import CodeGenBusiness
from backend.plugin.code_generator.schema.business import CreateCodeGenBusinessParam, UpdateCodeGenBusinessParam
from backend.utils.timezone import timezone


class CRUDCodeGenBusiness(CRUDPlus[CodeGenBusiness]):
    """Code generation business CRUD operations"""

    async def get(self, db: AsyncSession, pk: int) -> CodeGenBusiness | None:
        """
        Get code generation business definition

        :param db: Database session
        :param pk: Code generation business ID
        :return:
        """
        return await self.select_model(db, pk, deleted=0)

    async def get_by_name(self, db: AsyncSession, name: str) -> CodeGenBusiness | None:
        """
        Get code generation business definition by name

        :param db: Database session
        :param name: Table name
        :return:
        """
        return await self.select_model_by_column(db, table_name=name, deleted=0)

    async def get_all(self, db: AsyncSession) -> Sequence[CodeGenBusiness]:
        """
        Get all code generation business definitions

        :param db: Database session
        :return:
        """
        return await self.select_models(db, deleted=0)

    async def get_select(self, table_name: str | None) -> Select:
        """
        Get query expression for all code generation business definitions

        :param table_name: Business table name
        :return:
        """
        filters = {'deleted': 0}

        if table_name is not None:
            filters['table_name__like'] = f'%{table_name}%'

        return await self.select_order('id', 'desc', **filters)

    async def create(self, db: AsyncSession, obj: CreateCodeGenBusinessParam) -> None:
        """
        Create code generation business definition

        :param db: Database session
        :param obj: Code generation business creation parameters
        :return:
        """
        await self.create_model(db, obj)

    async def update(self, db: AsyncSession, pk: int, obj: UpdateCodeGenBusinessParam) -> int:
        """
        Update code generation business definition

        :param db: Database session
        :param pk: Code generation business ID
        :param obj: Code generation business update parameters
        :return:
        """
        return await self.update_model_by_column(db, obj, id=pk, deleted=0)

    async def delete(self, db: AsyncSession, pk: int) -> int:
        """
        Delete code generation business definition

        :param db: Database session
        :param pk: Code generation business ID
        :return:
        """
        return await self.delete_model_by_column(
            db,
            logical_deletion=True,
            deleted_flag_column='deleted',
            deleted_flag_value=self.model.id,
            deleted_at_column='deleted_time',
            deleted_at_factory=timezone.now(),
            id=pk,
            deleted=0,
        )


code_gen_business_dao: CRUDCodeGenBusiness = CRUDCodeGenBusiness(CodeGenBusiness)
