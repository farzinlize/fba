from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, Request

from backend.app.admin.schema.menu import CreateMenuParam, GetMenuDetail, GetMenuTree, UpdateMenuParam
from backend.app.admin.service.menu_service import menu_service
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter()


@router.get(
    '/sidebar',
    summary='Get user sidebar menus',
    description='Compatible with vben admin v5',
    dependencies=[DependsJwtAuth],
)
async def get_user_sidebar(db: CurrentSession, request: Request) -> ResponseSchemaModel[list[dict[str, Any] | None]]:
    menu = await menu_service.get_sidebar(db=db, request=request)
    return response_base.success(data=menu)


@router.get('/{pk}', summary='Get menu details', dependencies=[DependsJwtAuth])
async def get_menu(
    db: CurrentSession, pk: Annotated[int, Path(description='Menu ID')]
) -> ResponseSchemaModel[GetMenuDetail]:
    data = await menu_service.get(db=db, pk=pk)
    return response_base.success(data=data)


@router.get('', summary='Get menu tree', dependencies=[DependsJwtAuth])
async def get_menu_tree(
    db: CurrentSession,
    title: Annotated[str | None, Query(description='Menu title')] = None,
    status: Annotated[int | None, Query(description='Status')] = None,
) -> ResponseSchemaModel[list[GetMenuTree]]:
    menu = await menu_service.get_tree(db=db, title=title, status=status)
    return response_base.success(data=menu)


@router.post(
    '',
    summary='Create menu',
    dependencies=[
        Depends(RequestPermission('sys:menu:add')),
        DependsRBAC,
    ],
)
async def create_menu(db: CurrentSessionTransaction, obj: CreateMenuParam) -> ResponseModel:
    await menu_service.create(db=db, obj=obj)
    return response_base.success()


@router.put(
    '/{pk}',
    summary='Update menu',
    dependencies=[
        Depends(RequestPermission('sys:menu:edit')),
        DependsRBAC,
    ],
)
async def update_menu(
    db: CurrentSessionTransaction, pk: Annotated[int, Path(description='Menu ID')], obj: UpdateMenuParam
) -> ResponseModel:
    count = await menu_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    '/{pk}',
    summary='Delete menu',
    dependencies=[
        Depends(RequestPermission('sys:menu:del')),
        DependsRBAC,
    ],
)
async def delete_menu(db: CurrentSessionTransaction, pk: Annotated[int, Path(description='Menu ID')]) -> ResponseModel:
    count = await menu_service.delete(db=db, pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()
