from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.exception import errors
from backend.common.pagination import paging_data
from backend.plugin.notice.crud.crud_notice import notice_dao
from backend.plugin.notice.model import Notice
from backend.plugin.notice.schema.notice import CreateNoticeParam, DeleteNoticeParam, UpdateNoticeParam


class NoticeService:
    """Notice service"""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> Notice:
        """
        Get notice

        :param db: Database session
        :param pk: Notice ID
        :return:
        """

        notice = await notice_dao.get(db, pk)
        if not notice:
            raise errors.NotFoundError(msg='Notice does not exist')
        return notice

    @staticmethod
    async def get_list(db: AsyncSession, title: str | None, type: int | None, status: int | None) -> dict[str, Any]:
        """
        Get notice list

        :param db: Database session
        :param title: Notice title
        :param type: Notice type
        :param status: Notice status
        :return:
        """
        notice_select = await notice_dao.get_select(title, type, status)
        return await paging_data(db, notice_select)

    @staticmethod
    async def get_all(*, db: AsyncSession) -> Sequence[Notice]:
        """
        Get all notices

        :param db: Database session
        :return:
        """

        notices = await notice_dao.get_all(db)
        return notices

    @staticmethod
    async def create(*, db: AsyncSession, obj: CreateNoticeParam) -> None:
        """
        Create notice

        :param db: Database session
        :param obj: Notice creation parameters
        :return:
        """

        await notice_dao.create(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateNoticeParam) -> int:
        """
        Update notice

        :param db: Database session
        :param pk: Notice ID
        :param obj: Notice update parameters
        :return:
        """

        notice = await notice_dao.get(db, pk)
        if not notice:
            raise errors.NotFoundError(msg='Notice does not exist')
        count = await notice_dao.update(db, pk, obj)
        return count

    @staticmethod
    async def delete(*, db: AsyncSession, obj: DeleteNoticeParam) -> int:
        """
        Delete notices in bulk

        :param db: Database session
        :param obj: Notice ID list
        :return:
        """

        count = await notice_dao.delete(db, obj.pks)
        return count


notice_service: NoticeService = NoticeService()
