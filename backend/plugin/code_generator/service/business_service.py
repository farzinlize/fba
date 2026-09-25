from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.exception import errors
from backend.common.pagination import paging_data
from backend.plugin.code_generator.crud.crud_business import code_gen_business_dao
from backend.plugin.code_generator.model import CodeGenBusiness
from backend.plugin.code_generator.schema.business import CreateCodeGenBusinessParam, UpdateCodeGenBusinessParam


class CodeGenBusinessService:
    """Code generation business service"""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> CodeGenBusiness:
        """
        Get business definition by ID

        :param db: Database session
        :param pk: Business definition ID
        :return:
        """

        business = await code_gen_business_dao.get(db, pk)
        if not business:
            raise errors.NotFoundError(msg='Code generation business definition does not exist')
        return business

    @staticmethod
    async def get_all(*, db: AsyncSession) -> Sequence[CodeGenBusiness]:
        """
        Get all business definitions

        :param db: Database session
        :return:
        """

        return await code_gen_business_dao.get_all(db)

    @staticmethod
    async def get_list(*, db: AsyncSession, table_name: str) -> dict[str, Any]:
        """
        Get code generation business list

        :param db: Database session
        :param table_name: Business table name
        :return:
        """
        business_select = await code_gen_business_dao.get_select(table_name=table_name)
        return await paging_data(db, business_select)

    @staticmethod
    async def create(*, db: AsyncSession, obj: CreateCodeGenBusinessParam) -> None:
        """
        Create business definition

        :param db: Database session
        :param obj: Business definition creation parameters
        :return:
        """

        business = await code_gen_business_dao.get_by_name(db, obj.table_name)
        if business:
            raise errors.ConflictError(msg='Code generation business definition already exists')
        await code_gen_business_dao.create(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateCodeGenBusinessParam) -> int:
        """
        Update business definition

        :param db: Database session
        :param pk: Business definition ID
        :param obj: Business definition update parameters
        :return:
        """

        business = await code_gen_business_dao.get(db, pk)
        if not business:
            raise errors.NotFoundError(msg='Code generation business definition does not exist')
        if business.table_name != obj.table_name and await code_gen_business_dao.get_by_name(db, obj.table_name):
            raise errors.ConflictError(msg='Code generation business definition already exists')
        return await code_gen_business_dao.update(db, pk, obj)

    @staticmethod
    async def delete(*, db: AsyncSession, pk: int) -> int:
        """
        Delete business definition

        :param db: Database session
        :param pk: Business definition ID
        :return:
        """

        business = await code_gen_business_dao.get(db, pk)
        if not business:
            raise errors.NotFoundError(msg='Code generation business definition does not exist')
        return await code_gen_business_dao.delete(db, pk)


code_gen_business_service: CodeGenBusinessService = CodeGenBusinessService()
