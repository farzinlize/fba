from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_login_log import login_log_dao
from backend.app.admin.schema.login_log import CreateLoginLogParam, DeleteLoginLogParam
from backend.common.context import ctx
from backend.common.log import log
from backend.common.pagination import paging_data
from backend.database.db import async_db_session


class LoginLogService:
    """Login log service"""

    @staticmethod
    async def get_list(*, db: AsyncSession, username: str | None, status: int | None, ip: str | None) -> dict[str, Any]:
        """
        Get login log list

        :param db: Database session
        :param username: Username
        :param status: Status
        :param ip: IP address
        :return:
        """
        log_select = await login_log_dao.get_select(username=username, status=status, ip=ip)
        return await paging_data(db, log_select)

    @staticmethod
    async def create(
        *,
        user_uuid: str,
        username: str,
        login_time: datetime,
        status: int,
        msg: str,
    ) -> None:
        """
        Create login log

        :param user_uuid: User UUID
        :param username: Username
        :param login_time: Login time
        :param status: Status
        :param msg: Message
        :return:
        """
        try:
            obj = CreateLoginLogParam(
                user_uuid=user_uuid,
                username=username,
                status=status,
                ip=ctx.ip,
                country=ctx.country,
                region=ctx.region,
                city=ctx.city,
                user_agent=ctx.user_agent,
                browser=ctx.browser,
                os=ctx.os,
                device=ctx.device,
                msg=msg,
                login_time=login_time,
            )
            # Create a separate database session for the background task
            async with async_db_session.begin() as db:
                await login_log_dao.create(db, obj)
        except Exception as e:
            log.error(f'Failed to create login log: {e}')

    @staticmethod
    async def delete(*, db: AsyncSession, obj: DeleteLoginLogParam) -> int:
        """
        Delete login logs in bulk

        :param db: Database session
        :param obj: Log ID list
        :return:
        """
        count = await login_log_dao.delete(db, obj.pks)
        return count

    @staticmethod
    async def delete_all(*, db: AsyncSession) -> None:
        """Clear all login logs"""
        await login_log_dao.delete_all(db)


login_log_service: LoginLogService = LoginLogService()
