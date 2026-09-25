from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.enums import DataBaseType
from backend.common.exception import errors
from backend.core.conf import settings
from backend.plugin.code_generator.crud.crud_business import code_gen_business_dao
from backend.plugin.code_generator.crud.crud_column import code_gen_column_dao
from backend.plugin.code_generator.enums import GenMySQLColumnType, GenPostgreSQLColumnType
from backend.plugin.code_generator.model import CodeGenColumn
from backend.plugin.code_generator.schema.column import CreateCodeGenColumnParam, UpdateCodeGenColumnParam
from backend.plugin.code_generator.utils.type_conversion import sql_type_to_pydantic


class CodeGenColumnService:
    """Code generation model column service"""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> CodeGenColumn:
        """
        Get model column by ID

        :param db: Database session
        :param pk: Model column ID
        :return:
        """

        column = await code_gen_column_dao.get(db, pk)
        if not column:
            raise errors.NotFoundError(msg='Code generation model column does not exist')
        if not await code_gen_business_dao.get(db, column.code_gen_business_id):
            raise errors.NotFoundError(msg='Code generation business definition does not exist')
        return column

    @staticmethod
    async def get_types() -> list[str]:
        """Get all column types"""
        if DataBaseType.mysql == settings.DATABASE_TYPE:
            types = GenMySQLColumnType.get_member_keys()
        else:
            types = GenPostgreSQLColumnType.get_member_keys()
        types.sort()
        return types

    @staticmethod
    async def get_columns(*, db: AsyncSession, business_id: int) -> Sequence[CodeGenColumn]:
        """
        Get all model columns for a business definition

        :param db: Database session
        :param business_id: Business definition ID
        :return:
        """

        if not await code_gen_business_dao.get(db, business_id):
            raise errors.NotFoundError(msg='Code generation business definition does not exist')
        return await code_gen_column_dao.get_all_by_business(db, business_id)

    @staticmethod
    async def create(*, db: AsyncSession, obj: CreateCodeGenColumnParam) -> None:
        """
        Create model column

        :param db: Database session
        :param obj: Model column creation parameters
        :return:
        """

        if not await code_gen_business_dao.get(db, obj.code_gen_business_id):
            raise errors.NotFoundError(msg='Code generation business definition does not exist')

        code_gen_columns = await code_gen_column_dao.get_all_by_business(db, obj.code_gen_business_id)
        if obj.name in [code_gen_column.name for code_gen_column in code_gen_columns]:
            raise errors.ForbiddenError(msg='Model column already exists')

        pd_type = sql_type_to_pydantic(obj.type)
        await code_gen_column_dao.create(db, obj, pd_type=pd_type)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateCodeGenColumnParam) -> int:
        """
        Update model column

        :param db: Database session
        :param pk: Model column ID
        :param obj: Model column update parameters
        :return:
        """

        column = await code_gen_column_dao.get(db, pk)
        if not column:
            raise errors.NotFoundError(msg='Code generation model column does not exist')
        if not await code_gen_business_dao.get(db, column.code_gen_business_id):
            raise errors.NotFoundError(msg='Code generation business definition does not exist')
        if not await code_gen_business_dao.get(db, obj.code_gen_business_id):
            raise errors.NotFoundError(msg='Code generation business definition does not exist')
        if obj.name != column.name:
            code_gen_columns = await code_gen_column_dao.get_all_by_business(db, obj.code_gen_business_id)
            if obj.name in [code_gen_column.name for code_gen_column in code_gen_columns]:
                raise errors.ConflictError(msg='Model column name already exists')

        pd_type = sql_type_to_pydantic(obj.type)
        return await code_gen_column_dao.update(db, pk, obj, pd_type=pd_type)

    @staticmethod
    async def delete(*, db: AsyncSession, pk: int) -> int:
        """
        Delete model column

        :param db: Database session
        :param pk: Model column ID
        :return:
        """

        column = await code_gen_column_dao.get(db, pk)
        if not column:
            raise errors.NotFoundError(msg='Code generation model column does not exist')
        if not await code_gen_business_dao.get(db, column.code_gen_business_id):
            raise errors.NotFoundError(msg='Code generation business definition does not exist')
        return await code_gen_column_dao.delete(db, pk)


code_gen_column_service: CodeGenColumnService = CodeGenColumnService()
