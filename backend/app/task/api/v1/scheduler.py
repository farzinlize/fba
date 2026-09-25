from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from backend.app.task.schema.scheduler import (
    CreateTaskSchedulerParam,
    GetTaskSchedulerDetail,
    UpdateTaskSchedulerParam,
)
from backend.app.task.service.scheduler_service import task_scheduler_service
from backend.common.pagination import DependsPagination, PageData
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter()


@router.get('/all', summary='Get all task schedules', dependencies=[DependsJwtAuth])
async def get_all_task_schedulers(db: CurrentSession) -> ResponseSchemaModel[list[GetTaskSchedulerDetail]]:
    schedulers = await task_scheduler_service.get_all(db=db)
    return response_base.success(data=schedulers)


@router.get('/{pk}', summary='Get task schedule details', dependencies=[DependsJwtAuth])
async def get_task_scheduler(
    db: CurrentSession,
    pk: Annotated[int, Path(description='Task schedule ID')],
) -> ResponseSchemaModel[GetTaskSchedulerDetail]:
    task_scheduler = await task_scheduler_service.get(db=db, pk=pk)
    return response_base.success(data=task_scheduler)


@router.get(
    '',
    summary='Get all task schedules with pagination',
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_task_scheduler_paginated(
    db: CurrentSession,
    name: Annotated[str | None, Query(description='Task schedule name')] = None,
    type: Annotated[int | None, Query(description='Task schedule type')] = None,
) -> ResponseSchemaModel[PageData[GetTaskSchedulerDetail]]:
    page_data = await task_scheduler_service.get_list(db=db, name=name, type=type)
    return response_base.success(data=page_data)


@router.post(
    '',
    summary='Create task schedule',
    dependencies=[
        Depends(RequestPermission('sys:task:add')),
        DependsRBAC,
    ],
)
async def create_task_scheduler(db: CurrentSessionTransaction, obj: CreateTaskSchedulerParam) -> ResponseModel:
    await task_scheduler_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    '/{pk}',
    summary='Update task schedule',
    dependencies=[
        Depends(RequestPermission('sys:task:edit')),
        DependsRBAC,
    ],
)
async def update_task_scheduler(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description='Task schedule ID')],
    obj: UpdateTaskSchedulerParam,
) -> ResponseModel:
    count = await task_scheduler_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put(
    '/{pk}/status',
    summary='Update task schedule status',
    dependencies=[
        Depends(RequestPermission('sys:task:edit')),
        DependsRBAC,
    ],
)
async def update_task_scheduler_status(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description='Task schedule ID')]
) -> ResponseModel:
    count = await task_scheduler_service.update_status(db=db, pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    '/{pk}',
    summary='Delete task schedule',
    dependencies=[
        Depends(RequestPermission('sys:task:del')),
        DependsRBAC,
    ],
)
async def delete_task_scheduler(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description='Task schedule ID')]
) -> ResponseModel:
    count = await task_scheduler_service.delete(db=db, pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.post(
    '/{pk}/execute',
    summary='Execute task',
    dependencies=[
        Depends(RequestPermission('sys:task:exec')),
        DependsRBAC,
    ],
)
async def execute_task(db: CurrentSession, pk: Annotated[int, Path(description='Task schedule ID')]) -> ResponseModel:
    await task_scheduler_service.execute(db=db, pk=pk)
    return response_base.success()
