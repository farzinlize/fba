from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, Request

from backend.app.admin.schema.role import GetRoleDetail
from backend.app.admin.schema.user import (
    AddUserParam,
    GetCurrentUserInfoWithRelationDetail,
    GetUserInfoWithRelationDetail,
    ResetPasswordParam,
    UpdateUserParam,
)
from backend.app.admin.service.user_service import user_service
from backend.common.enums import UserPermissionType
from backend.common.pagination import DependsPagination, PageData
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth, DependsSuperUser
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession, CurrentSessionTransaction

router = APIRouter()


@router.get('/me', summary='Get current user information', dependencies=[DependsJwtAuth])
async def get_current_user(request: Request) -> ResponseSchemaModel[GetCurrentUserInfoWithRelationDetail]:
    data = request.user.model_dump()
    return response_base.success(data=data)


@router.get('/{pk}', summary='Get user information', dependencies=[DependsJwtAuth])
async def get_userinfo(
    db: CurrentSession,
    pk: Annotated[int, Path(description='User ID')],
) -> ResponseSchemaModel[GetUserInfoWithRelationDetail]:
    data = await user_service.get_userinfo(db=db, pk=pk)
    return response_base.success(data=data)


@router.get('/{pk}/roles', summary='Get all user roles', dependencies=[DependsJwtAuth])
async def get_user_roles(
    db: CurrentSession, pk: Annotated[int, Path(description='User ID')]
) -> ResponseSchemaModel[list[GetRoleDetail]]:
    data = await user_service.get_roles(db=db, pk=pk)
    return response_base.success(data=data)


@router.get(
    '',
    summary='Get all users with pagination',
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_users_paginated(
    db: CurrentSession,
    dept: Annotated[int | None, Query(description='Department ID')] = None,
    username: Annotated[str | None, Query(description='Username')] = None,
    phone: Annotated[str | None, Query(description='Mobile number')] = None,
    status: Annotated[int | None, Query(description='Status')] = None,
) -> ResponseSchemaModel[PageData[GetUserInfoWithRelationDetail]]:
    page_data = await user_service.get_list(db=db, dept=dept, username=username, phone=phone, status=status)
    return response_base.success(data=page_data)


@router.post('', summary='Create user', dependencies=[DependsSuperUser])
async def create_user(
    db: CurrentSessionTransaction, obj: AddUserParam
) -> ResponseSchemaModel[GetUserInfoWithRelationDetail]:
    await user_service.create(db=db, obj=obj)
    data = await user_service.get_userinfo(db=db, username=obj.username)
    return response_base.success(data=data)


@router.put('/{pk}', summary='Update user information', dependencies=[DependsSuperUser])
async def update_user(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description='User ID')],
    obj: UpdateUserParam,
) -> ResponseModel:
    count = await user_service.update(db=db, pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put('/{pk}/permissions', summary='Update user permissions', dependencies=[DependsSuperUser])
async def update_user_permission(
    db: CurrentSessionTransaction,
    request: Request,
    pk: Annotated[int, Path(description='User ID')],
    type: Annotated[UserPermissionType, Query(description='Permission type')],
) -> ResponseModel:
    count = await user_service.update_permission(db=db, request=request, pk=pk, type=type)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put('/me/password', summary='Update current user password', dependencies=[DependsJwtAuth])
async def update_user_password(
    db: CurrentSessionTransaction, request: Request, obj: ResetPasswordParam
) -> ResponseModel:
    count = await user_service.update_password(db=db, user_id=request.user.id, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put('/{pk}/password', summary='Reset user password', dependencies=[DependsSuperUser])
async def reset_user_password(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description='User ID')],
    password: Annotated[str, Body(embed=True, description='New password')],
) -> ResponseModel:
    count = await user_service.reset_password(db=db, pk=pk, password=password)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put('/me/nickname', summary='Update current user nickname', dependencies=[DependsJwtAuth])
async def update_user_nickname(
    db: CurrentSessionTransaction,
    request: Request,
    nickname: Annotated[str, Body(embed=True, description='User nickname')],
) -> ResponseModel:
    count = await user_service.update_nickname(db=db, user_id=request.user.id, nickname=nickname)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put('/me/avatar', summary='Update current user avatar', dependencies=[DependsJwtAuth])
async def update_user_avatar(
    db: CurrentSessionTransaction,
    request: Request,
    avatar: Annotated[str, Body(embed=True, description='User avatar URL')],
) -> ResponseModel:
    count = await user_service.update_avatar(db=db, user_id=request.user.id, avatar=avatar)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put('/me/email', summary='Update current user email', dependencies=[DependsJwtAuth])
async def update_user_email(
    db: CurrentSessionTransaction,
    request: Request,
    captcha: Annotated[str, Body(embed=True, description='Email verification code')],
    email: Annotated[str, Body(embed=True, description='User email')],
) -> ResponseModel:
    count = await user_service.update_email(db=db, user_id=request.user.id, captcha=captcha, email=email)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    path='/{pk}',
    summary='Delete user',
    dependencies=[
        Depends(RequestPermission('sys:user:del')),
        DependsRBAC,
    ],
)
async def delete_user(db: CurrentSessionTransaction, pk: Annotated[int, Path(description='User ID')]) -> ResponseModel:
    count = await user_service.delete(db=db, pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()
