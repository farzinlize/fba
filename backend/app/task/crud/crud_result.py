from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.task.model import TaskResult


class CRUDTaskResult(CRUDPlus[TaskResult]):
    """Task result database operations"""

    async def get(self, db: AsyncSession, pk: int) -> TaskResult | None:
        """
        Get task result details

        :param db: Database session
        :param pk: Task ID
        :return:
        """
        return await self.select_model(db, pk)

    async def get_select(self, name: str | None, task_id: str | None) -> Select:
        """
        Get the query expression for the task result list

        :param name: Task name
        :param task_id: Task ID
        :return:
        """
        filters = {}

        if name is not None:
            filters['name__like'] = f'%{name}%'
        if task_id is not None:
            filters['task_id'] = task_id

        return await self.select_order('id', 'desc', **filters)

    async def delete(self, db: AsyncSession, pks: list[int]) -> int:
        """
        Delete task results in bulk

        :param db: Database session
        :param pks: Task result ID list
        :return:
        """
        return await self.delete_model_by_column(db, allow_multiple=True, id__in=pks)


task_result_dao: CRUDTaskResult = CRUDTaskResult(TaskResult)
