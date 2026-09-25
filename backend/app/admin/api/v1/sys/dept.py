from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import ColumnElement

from backend.app.admin.model import Dept
from backend.app.admin.schema.dept import CreateDeptParam, GetDeptDetail, GetDeptTree, UpdateDeptParam
from backend.app.admin.service.dept_service import dept_service
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import DataPermissionFilter, RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter()


@router.get('/{pk}', summary='Get department details', dependencies=[DependsJwtAuth])
async def get_dept(
    db: CurrentSession, pk: Annotated[int, Path(description='Department ID')]
) -> ResponseSchemaModel[GetDeptDetail]:
    data = await dept_service.get(db=db, pk=pk)
    return response_base.success(data=data)


@router.get('', summary='Get department tree', dependencies=[DependsJwtAuth])
async def get_dept_tree(
    db: CurrentSession,
    data_filter: Annotated[ColumnElement[bool], Depends(DataPermissionFilter(Dept))],
    name: Annotated[str | None, Query(description='Department name')] = None,
    leader: Annotated[str | None, Query(description='Department manager')] = None,
    phone: Annotated[str | None, Query(description='Contact phone number')] = None,
    status: Annotated[int | None, Query(description='Status')] = None,
) -> ResponseSchemaModel[list[GetDeptTree]]:
    dept = await dept_service.get_tree(
        db=db, data_filter=data_filter, name=name, leader=leader, phone=phone, status=status
    )
    return response_base.success(data=dept)


@router.post(
    '',
    summary='Create department',
    dependencies=[
        Depends(RequestPermission('sys:dept:add')),
        DependsRBAC,
    ],
)
async def create_dept(db: CurrentSessionTransaction, obj: CreateDeptParam) -> ResponseModel:
    await dept_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    '/{pk}',
    summary='Update department',
    dependencies=[
        Depends(RequestPermission('sys:dept:edit')),
        DependsRBAC,
    ],
)
async def update_dept(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description='Department ID')], obj: UpdateDeptParam
) -> ResponseModel:
    count = await dept_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    '/{pk}',
    summary='Delete department',
    dependencies=[
        Depends(RequestPermission('sys:dept:del')),
        DependsRBAC,
    ],
)
async def delete_dept(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description='Department ID')]
) -> ResponseModel:
    count = await dept_service.delete(db=db, pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()
