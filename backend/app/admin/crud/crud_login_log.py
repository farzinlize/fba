from sqlalchemy import Select
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model import LoginLog
from backend.app.admin.schema.login_log import CreateLoginLogParam


class CRUDLoginLog(CRUDPlus[LoginLog]):
    """Login log database operations"""

    async def get_select(self, username: str | None, status: int | None, ip: str | None) -> Select:
        """
        Get the query expression for the login log list

        :param username: Username
        :param status: Login status
        :param ip: IP address
        :return:
        """
        filters = {}

        if username is not None:
            filters['username__like'] = f'%{username}%'
        if status is not None:
            filters['status'] = status
        if ip is not None:
            filters['ip__like'] = f'%{ip}%'

        return await self.select_order('created_time', 'desc', **filters)

    async def create(self, db: AsyncSession, obj: CreateLoginLogParam) -> None:
        """
        Create login log

        :param db: Database session
        :param obj: Login log creation parameters
        :return:
        """
        await self.create_model(db, obj, commit=True)

    async def delete(self, db: AsyncSession, pks: list[int]) -> int:
        """
        Delete login logs in bulk

        :param db: Database session
        :param pks: Login log ID list
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
        await db.execute(sa_delete(LoginLog))


login_log_dao: CRUDLoginLog = CRUDLoginLog(LoginLog)
