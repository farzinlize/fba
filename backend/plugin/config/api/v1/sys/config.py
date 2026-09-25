from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query

from backend.common.pagination import DependsPagination, PageData
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.plugin.config.schema.config import (
    CreateConfigParam,
    GetConfigDetail,
    UpdateConfigParam,
    UpdateConfigsParam,
)
from backend.plugin.config.service.config_service import config_service

router = APIRouter()


@router.get('/all', summary='Get all configuration parameters', dependencies=[DependsJwtAuth])
async def get_all_configs(
    db: CurrentSession,
    type: Annotated[str | None, Query(description='Configuration parameter type')] = None,
) -> ResponseSchemaModel[list[GetConfigDetail]]:
    configs = await config_service.get_all(db=db, type=type)
    return response_base.success(data=configs)


@router.get('/{pk}', summary='Get configuration parameter details', dependencies=[DependsJwtAuth])
async def get_config(
    db: CurrentSession, pk: Annotated[int, Path(description='Configuration parameter ID')]
) -> ResponseSchemaModel[GetConfigDetail]:
    config = await config_service.get(db=db, pk=pk)
    return response_base.success(data=config)


@router.get(
    '',
    summary='Get all configuration parameters with pagination',
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_configs_paginated(
    db: CurrentSession,
    name: Annotated[str | None, Query(description='Configuration parameter name')] = None,
    type: Annotated[str | None, Query(description='Configuration parameter type')] = None,
) -> ResponseSchemaModel[PageData[GetConfigDetail]]:
    page_data = await config_service.get_list(db=db, name=name, type=type)
    return response_base.success(data=page_data)


@router.post(
    '',
    summary='Create configuration parameter',
    dependencies=[
        Depends(RequestPermission('sys:config:add')),
        DependsRBAC,
    ],
)
async def create_config(db: CurrentSessionTransaction, obj: CreateConfigParam) -> ResponseModel:
    await config_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    '',
    summary='Update configuration parameters in bulk',
    dependencies=[Depends(RequestPermission('sys.config.edits')), DependsRBAC],
)
async def bulk_update_config(db: CurrentSessionTransaction, objs: list[UpdateConfigsParam]) -> ResponseModel:
    count = await config_service.bulk_update(db=db, objs=objs)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put(
    '/{pk}',
    summary='Update configuration parameter',
    dependencies=[
        Depends(RequestPermission('sys:config:edit')),
        DependsRBAC,
    ],
)
async def update_config(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description='Configuration parameter ID')],
    obj: UpdateConfigParam,
) -> ResponseModel:
    count = await config_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    '',
    summary='Delete configuration parameters in bulk',
    dependencies=[
        Depends(RequestPermission('sys:config:del')),
        DependsRBAC,
    ],
)
async def delete_configs(
    db: CurrentSessionTransaction, pks: Annotated[list[int], Body(description='Configuration parameter ID list')]
) -> ResponseModel:
    count = await config_service.delete(db=db, pks=pks)
    if count > 0:
        return response_base.success()
    return response_base.fail()
