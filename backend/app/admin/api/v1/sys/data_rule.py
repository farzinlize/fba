from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from backend.app.admin.schema.data_rule import (
    CreateDataRuleParam,
    DeleteDataRuleParam,
    GetDataRuleColumnDetail,
    GetDataRuleDetail,
    GetDataRuleTemplateVariableDetail,
    UpdateDataRuleParam,
)
from backend.app.admin.service.data_rule_service import data_rule_service
from backend.common.pagination import DependsPagination, PageData
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter()


@router.get('/models', summary='Get available models for data rules', dependencies=[DependsJwtAuth])
async def get_data_rule_models() -> ResponseSchemaModel[list[str]]:
    models = await data_rule_service.get_models()
    return response_base.success(data=models)


@router.get(
    '/models/{model}/columns', summary='Get available model columns for data rules', dependencies=[DependsJwtAuth]
)
async def get_data_rule_model_columns(
    model: Annotated[str, Path(description='Model name')],
) -> ResponseSchemaModel[list[GetDataRuleColumnDetail]]:
    models = await data_rule_service.get_columns(model=model)
    return response_base.success(data=models)


@router.get(
    '/value-template-variables',
    summary='Get available template variables for data rule values',
    dependencies=[DependsJwtAuth],
)
async def get_data_rule_value_template_variables() -> ResponseSchemaModel[list[GetDataRuleTemplateVariableDetail]]:
    variables = await data_rule_service.get_value_template_variables()
    return response_base.success(data=variables)


@router.get('/all', summary='Get all data rules', dependencies=[DependsJwtAuth])
async def get_all_data_rules(db: CurrentSession) -> ResponseSchemaModel[list[GetDataRuleDetail]]:
    data = await data_rule_service.get_all(db=db)
    return response_base.success(data=data)


@router.get('/{pk}', summary='Get data rule details', dependencies=[DependsJwtAuth])
async def get_data_rule(
    db: CurrentSession,
    pk: Annotated[int, Path(description='Data rule ID')],
) -> ResponseSchemaModel[GetDataRuleDetail]:
    data = await data_rule_service.get(db=db, pk=pk)
    return response_base.success(data=data)


@router.get(
    '',
    summary='Get all data rules with pagination',
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_data_rules_paginated(
    db: CurrentSession,
    name: Annotated[str | None, Query(description='Rule name')] = None,
) -> ResponseSchemaModel[PageData[GetDataRuleDetail]]:
    page_data = await data_rule_service.get_list(db=db, name=name)
    return response_base.success(data=page_data)


@router.post(
    '',
    summary='Create data rule',
    dependencies=[
        Depends(RequestPermission('data:rule:add')),
        DependsRBAC,
    ],
)
async def create_data_rule(db: CurrentSessionTransaction, obj: CreateDataRuleParam) -> ResponseModel:
    await data_rule_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    '/{pk}',
    summary='Update data rule',
    dependencies=[
        Depends(RequestPermission('data:rule:edit')),
        DependsRBAC,
    ],
)
async def update_data_rule(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description='Data rule ID')],
    obj: UpdateDataRuleParam,
) -> ResponseModel:
    count = await data_rule_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    '',
    summary='Delete data rules in bulk',
    dependencies=[
        Depends(RequestPermission('data:rule:del')),
        DependsRBAC,
    ],
)
async def delete_data_rules(db: CurrentSessionTransaction, obj: DeleteDataRuleParam) -> ResponseModel:
    count = await data_rule_service.delete(db=db, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()
