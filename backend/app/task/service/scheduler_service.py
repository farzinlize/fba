import json

from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from backend.app.task.celery import celery_app
from backend.app.task.crud.crud_scheduler import task_scheduler_dao
from backend.app.task.enums import TaskSchedulerType
from backend.app.task.model import TaskScheduler
from backend.app.task.schema.scheduler import CreateTaskSchedulerParam, UpdateTaskSchedulerParam
from backend.app.task.utils.tzcrontab import crontab_verify
from backend.common.enums import StatusType
from backend.common.exception import errors
from backend.common.pagination import paging_data


class TaskSchedulerService:
    """Task schedule service"""

    @staticmethod
    async def get(*, db: AsyncSession, pk: int) -> TaskScheduler | None:
        """
        Get task schedule details

        :param db: Database session
        :param pk: Task schedule ID
        :return:
        """

        task_scheduler = await task_scheduler_dao.get(db, pk)
        if not task_scheduler:
            raise errors.NotFoundError(msg='Task schedule does not exist')
        return task_scheduler

    @staticmethod
    async def get_all(*, db: AsyncSession) -> Sequence[TaskScheduler]:
        """
        Get all task schedules

        :param db: Database session
        :return:
        """

        task_schedulers = await task_scheduler_dao.get_all(db)
        return task_schedulers

    @staticmethod
    async def get_list(*, db: AsyncSession, name: str | None, type: int | None) -> dict[str, Any]:
        """
        Get task schedule list

        :param db: Database session
        :param name: Task schedule name
        :param type: Task schedule type
        :return:
        """
        task_scheduler_select = await task_scheduler_dao.get_select(name=name, type=type)
        return await paging_data(db, task_scheduler_select)

    @staticmethod
    async def create(*, db: AsyncSession, obj: CreateTaskSchedulerParam) -> None:
        """
        Create task schedule

        :param db: Database session
        :param obj: Task schedule creation parameters
        :return:
        """

        task_scheduler = await task_scheduler_dao.get_by_name(db, obj.name)
        if task_scheduler:
            raise errors.ConflictError(msg='Task schedule already exists')
        if obj.type == TaskSchedulerType.CRONTAB:
            crontab_verify(obj.crontab)
        await task_scheduler_dao.create(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateTaskSchedulerParam) -> int:
        """
        Update task schedule

        :param db: Database session
        :param pk: Task schedule ID
        :param obj: Task schedule update parameters
        :return:
        """

        task_scheduler = await task_scheduler_dao.get(db, pk)
        if not task_scheduler:
            raise errors.NotFoundError(msg='Task schedule does not exist')
        if task_scheduler.name != obj.name and await task_scheduler_dao.get_by_name(db, obj.name):
            raise errors.ConflictError(msg='Task schedule already exists')
        if obj.type == TaskSchedulerType.CRONTAB:
            crontab_verify(obj.crontab)
        count = await task_scheduler_dao.update(db, pk, obj)
        return count

    @staticmethod
    async def update_status(*, db: AsyncSession, pk: int) -> int:
        """
        Update task schedule status

        :param db: Database session
        :param pk: Task schedule ID
        :return:
        """

        task_scheduler = await task_scheduler_dao.get(db, pk)
        if not task_scheduler:
            raise errors.NotFoundError(msg='Task schedule does not exist')
        next_status = StatusType.disable if task_scheduler.status == StatusType.enable else StatusType.enable
        count = await task_scheduler_dao.set_status(db, pk, status=next_status)
        return count

    @staticmethod
    async def delete(*, db: AsyncSession, pk: int) -> int:
        """
        Delete task schedule

        :param db: Database session
        :param pk: User ID
        :return:
        """

        task_scheduler = await task_scheduler_dao.get(db, pk)
        if not task_scheduler:
            raise errors.NotFoundError(msg='Task schedule does not exist')
        count = await task_scheduler_dao.delete(db, pk)
        return count

    @staticmethod
    async def execute(*, db: AsyncSession, pk: int) -> None:
        """
        Execute task

        :param db: Database session
        :param pk: Task schedule ID
        :return:
        """

        workers = await run_in_threadpool(celery_app.control.ping, timeout=0.5)
        if not workers:
            raise errors.ServerError(msg='Celery worker is temporarily unavailable; please try again later')
        task_scheduler = await task_scheduler_dao.get(db, pk)
        if not task_scheduler:
            raise errors.NotFoundError(msg='Task schedule does not exist')
        try:
            args = json.loads(task_scheduler.args) if task_scheduler.args else None
            kwargs = json.loads(task_scheduler.kwargs) if task_scheduler.kwargs else None
        except (TypeError, json.JSONDecodeError):
            raise errors.RequestError(msg='Execution failed: invalid task arguments')
        else:
            celery_app.send_task(name=task_scheduler.task, args=args, kwargs=kwargs)


task_scheduler_service: TaskSchedulerService = TaskSchedulerService()
