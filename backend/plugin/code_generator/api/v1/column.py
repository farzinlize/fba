from typing import Annotated

from fastapi import APIRouter, Depends, Path

from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.plugin.code_generator.schema.column import (
    CreateCodeGenColumnParam,
    GetCodeGenColumnDetail,
    UpdateCodeGenColumnParam,
)
from backend.plugin.code_generator.service.column_service import code_gen_column_service

router = APIRouter()


@router.get('/types', summary='Get code generation model column types', dependencies=[DependsJwtAuth])
async def get_column_types() -> ResponseSchemaModel[list[str]]:
    column_types = await code_gen_column_service.get_types()
    return response_base.success(data=column_types)


@router.get('/{pk}', summary='Get code generation model column details', dependencies=[DependsJwtAuth])
async def get_column(
    db: CurrentSession, pk: Annotated[int, Path(description='Model column ID')]
) -> ResponseSchemaModel[GetCodeGenColumnDetail]:
    data = await code_gen_column_service.get(db=db, pk=pk)
    return response_base.success(data=data)


@router.post(
    '',
    summary='Create code generation model column',
    dependencies=[
        Depends(RequestPermission('codegen:column:add')),
        DependsRBAC,
    ],
)
async def create_column(db: CurrentSessionTransaction, obj: CreateCodeGenColumnParam) -> ResponseModel:
    await code_gen_column_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    '/{pk}',
    summary='Update code generation model column',
    dependencies=[
        Depends(RequestPermission('codegen:column:edit')),
        DependsRBAC,
    ],
)
async def update_column(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description='Model column ID')],
    obj: UpdateCodeGenColumnParam,
) -> ResponseModel:
    count = await code_gen_column_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    '/{pk}',
    summary='Delete code generation model column',
    dependencies=[
        Depends(RequestPermission('codegen:column:del')),
        DependsRBAC,
    ],
)
async def delete_column(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description='Model column ID')]
) -> ResponseModel:
    count = await code_gen_column_service.delete(db=db, pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()
