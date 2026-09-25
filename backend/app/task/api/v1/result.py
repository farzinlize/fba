from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from backend.app.task.schema.result import DeleteTaskResultParam, GetTaskResultDetail
from backend.app.task.service.result_service import task_result_service
from backend.common.pagination import DependsPagination, PageData
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter()


@router.get('/{pk}', summary='Get task result details', dependencies=[DependsJwtAuth])
async def get_task_result(
    db: CurrentSession,
    pk: Annotated[int, Path(description='Task result ID')],
) -> ResponseSchemaModel[GetTaskResultDetail]:
    result = await task_result_service.get(db=db, pk=pk)
    return response_base.success(data=result)


@router.get(
    '',
    summary='Get all task results with pagination',
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_task_results_paginated(
    db: CurrentSession,
    name: Annotated[str | None, Query(description='Task name')] = None,
    task_id: Annotated[str | None, Query(description='Task ID')] = None,
) -> ResponseSchemaModel[PageData[GetTaskResultDetail]]:
    page_data = await task_result_service.get_list(db=db, name=name, task_id=task_id)
    return response_base.success(data=page_data)


@router.delete(
    '',
    summary='Delete task results in bulk',
    dependencies=[
        Depends(RequestPermission('sys:task:del')),
        DependsRBAC,
    ],
)
async def delete_task_result(db: CurrentSessionTransaction, obj: DeleteTaskResultParam) -> ResponseModel:
    count = await task_result_service.delete(db=db, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()
