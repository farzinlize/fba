from sqlalchemy import Select
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model import OperaLog
from backend.app.admin.schema.opera_log import CreateOperaLogParam


class CRUDOperaLog(CRUDPlus[OperaLog]):
    """Operation log database operations"""

    async def get_select(self, username: str | None, status: int | None, ip: str | None) -> Select:
        """
        Get the query expression for the operation log list

        :param username: Username
        :param status: Operation status
        :param ip: IP address
        :return:
        """
        filters = {}

        if username is not None:
            filters['username__like'] = f'%{username}%'
        if status is not None:
            filters['status__eq'] = status
        if ip is not None:
            filters['ip__like'] = f'%{ip}%'

        return await self.select_order('created_time', 'desc', **filters)

    async def create(self, db: AsyncSession, obj: CreateOperaLogParam) -> None:
        """
        Create operation log

        :param db: Database session
        :param obj: Operation log creation parameters
        :return:
        """
        await self.create_model(db, obj)

    async def bulk_create(self, db: AsyncSession, objs: list[CreateOperaLogParam]) -> None:
        """
        Create operation logs in bulk

        :param db: Database session
        :param objs: List of operation log creation parameters
        :return:
        """
        await self.create_models(db, objs)

    async def delete(self, db: AsyncSession, pks: list[int]) -> int:
        """
        Delete operation logs in bulk

        :param db: Database session
        :param pks: Operation log ID list
        :return:
        """
        return await self.delete_model_by_column(db, allow_multiple=True, id__in=pks)

    @staticmethod
    async def delete_all(db: AsyncSession) -> None:
        """
        Delete all logs

        :param db: Database session
        :return:
        """
        await db.execute(sa_delete(OperaLog))


opera_log_dao: CRUDOperaLog = CRUDOperaLog(OperaLog)
