from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.task.crud.crud_result import task_result_dao
from backend.app.task.model import TaskResult
from backend.app.task.schema.result import DeleteTaskResultParam
from backend.common.exception import errors
from backend.common.pagination import paging_data


class TaskResultService:
    """Task result service"""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> TaskResult:
        """
        Get task result details

        :param db: Database session
        :param pk: Task ID
        :return:
        """

        result = await task_result_dao.get(db, pk)
        if not result:
            raise errors.NotFoundError(msg='Task result does not exist')
        return result

    @staticmethod
    async def get_list(*, db: AsyncSession, name: str | None, task_id: str | None) -> dict[str, Any]:
        """
        Get task result list

        :param db: Database session
        :param name: Task name
        :param task_id: Task ID
        :return:
        """
        result_select = await task_result_dao.get_select(name, task_id)
        return await paging_data(db, result_select)

    @staticmethod
    async def delete(*, db: AsyncSession, obj: DeleteTaskResultParam) -> int:
        """
        Delete task results in bulk

        :param db: Database session
        :param obj: Task result ID list
        :return:
        """

        count = await task_result_dao.delete(db, obj.pks)
        return count


task_result_service: TaskResultService = TaskResultService()
