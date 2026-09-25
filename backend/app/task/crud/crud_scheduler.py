from collections.abc import Sequence

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.task.model import TaskScheduler
from backend.app.task.schema.scheduler import CreateTaskSchedulerParam, UpdateTaskSchedulerParam
from backend.utils.timezone import timezone


class CRUDTaskScheduler(CRUDPlus[TaskScheduler]):
    """Task schedule database operations"""

    @staticmethod
    async def get(db: AsyncSession, pk: int) -> TaskScheduler | None:
        """
        Get task schedule

        :param db: Database session
        :param pk: Task schedule ID
        :return:
        """
        return await task_scheduler_dao.select_model(db, pk, deleted=0)

    async def get_all(self, db: AsyncSession) -> Sequence[TaskScheduler]:
        """
        Get all task schedules

        :param db: Database session
        :return:
        """
        return await self.select_models(db, deleted=0)

    async def get_select(self, name: str | None, type: int | None) -> Select:
        """
        Get the query expression for the task schedule list

        :param name: Task schedule name
        :param type: Task schedule type
        :return:
        """
        filters = {'deleted': 0}

        if name is not None:
            filters['name__like'] = f'%{name}%'
        if type is not None:
            filters['type'] = type

        return await self.select_order('id', **filters)

    async def get_by_name(self, db: AsyncSession, name: str) -> TaskScheduler | None:
        """
        Get task schedule by name

        :param db: Database session
        :param name: Task schedule name
        :return:
        """
        return await self.select_model_by_column(db, name=name, deleted=0)

    async def create(self, db: AsyncSession, obj: CreateTaskSchedulerParam) -> None:
        """
        Create task schedule

        :param db: Database session
        :param obj: Task schedule creation parameters
        :return:
        """
        await self.create_model(db, obj, flush=True)
        TaskScheduler.no_changes = False

    async def update(self, db: AsyncSession, pk: int, obj: UpdateTaskSchedulerParam) -> int:
        """
        Update task schedule

        :param db: Database session
        :param pk: Task schedule ID
        :param obj: Task schedule update parameters
        :return:
        """
        task_scheduler = await self.get(db, pk)
        for key, value in obj.model_dump(exclude_unset=True).items():
            setattr(task_scheduler, key, value)
        TaskScheduler.no_changes = False
        return 1

    async def set_status(self, db: AsyncSession, pk: int, *, status: int) -> int:
        """
        Set task schedule status

        :param db: Database session
        :param pk: Task schedule ID
        :param status: Status
        :return:
        """
        task_scheduler = await self.get(db, pk)
        task_scheduler.status = status
        TaskScheduler.no_changes = False
        return 1

    async def delete(self, db: AsyncSession, pk: int) -> int:
        """
        Delete task schedule

        :param db: Database session
        :param pk: Task schedule ID
        :return:
        """
        count = await self.delete_model_by_column(
            db,
            logical_deletion=True,
            deleted_flag_column='deleted',
            deleted_flag_value=self.model.id,
            deleted_at_column='deleted_time',
            deleted_at_factory=timezone.now(),
            id=pk,
            deleted=0,
        )
        if count:
            TaskScheduler.no_changes = False
        return count


task_scheduler_dao: CRUDTaskScheduler = CRUDTaskScheduler(TaskScheduler)
