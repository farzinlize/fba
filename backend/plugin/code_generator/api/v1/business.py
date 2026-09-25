from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from backend.common.pagination import DependsPagination, PageData
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.plugin.code_generator.schema.business import (
    CreateCodeGenBusinessParam,
    GetCodeGenBusinessDetail,
    UpdateCodeGenBusinessParam,
)
from backend.plugin.code_generator.schema.column import GetCodeGenColumnDetail
from backend.plugin.code_generator.service.business_service import code_gen_business_service
from backend.plugin.code_generator.service.column_service import code_gen_column_service

router = APIRouter()


@router.get('/all', summary='Get all code generation business definitions', dependencies=[DependsJwtAuth])
async def get_all_businesses(db: CurrentSession) -> ResponseSchemaModel[list[GetCodeGenBusinessDetail]]:
    data = await code_gen_business_service.get_all(db=db)
    return response_base.success(data=data)


@router.get('/{pk}', summary='Get code generation business details', dependencies=[DependsJwtAuth])
async def get_business(
    db: CurrentSession,
    pk: Annotated[int, Path(description='Business definition ID')],
) -> ResponseSchemaModel[GetCodeGenBusinessDetail]:
    data = await code_gen_business_service.get(db=db, pk=pk)
    return response_base.success(data=data)


@router.get(
    '',
    summary='Get all code generation business definitions with pagination',
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_businesses_paginated(
    db: CurrentSession,
    table_name: Annotated[str | None, Query(description='Code generation business table name')] = None,
) -> ResponseSchemaModel[PageData[GetCodeGenBusinessDetail]]:
    page_data = await code_gen_business_service.get_list(db=db, table_name=table_name)
    return response_base.success(data=page_data)


@router.get(
    '/{pk}/columns',
    summary='Get all model columns for a code generation business definition',
    dependencies=[DependsJwtAuth],
)
async def get_business_all_columns(
    db: CurrentSession,
    pk: Annotated[int, Path(description='Business definition ID')],
) -> ResponseSchemaModel[list[GetCodeGenColumnDetail]]:
    data = await code_gen_column_service.get_columns(db=db, business_id=pk)
    return response_base.success(data=data)


@router.post(
    '',
    summary='Create code generation business definition',
    dependencies=[
        Depends(RequestPermission('codegen:business:add')),
        DependsRBAC,
    ],
)
async def create_business(db: CurrentSessionTransaction, obj: CreateCodeGenBusinessParam) -> ResponseModel:
    await code_gen_business_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    '/{pk}',
    summary='Update code generation business definition',
    dependencies=[
        Depends(RequestPermission('codegen:business:edit')),
        DependsRBAC,
    ],
)
async def update_business(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description='Business definition ID')],
    obj: UpdateCodeGenBusinessParam,
) -> ResponseModel:
    count = await code_gen_business_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    '/{pk}',
    summary='Delete code generation business definition',
    dependencies=[
        Depends(RequestPermission('codegen:business:del')),
        DependsRBAC,
    ],
)
async def delete_business(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description='Business definition ID')]
) -> ResponseModel:
    count = await code_gen_business_service.delete(db=db, pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()
