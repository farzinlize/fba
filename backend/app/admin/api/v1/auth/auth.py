from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPBasicCredentials
from pyrate_limiter import Duration, Rate
from starlette.background import BackgroundTasks

from backend.app.admin.schema.token import GetLoginToken, GetNewToken, GetSwaggerToken
from backend.app.admin.schema.user import AuthLoginParam
from backend.app.admin.service.auth_service import auth_service
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import CurrentSession, CurrentSessionTransaction
from backend.utils.limiter import RateLimiter

router = APIRouter()


@router.post(
    '/login/swagger',
    summary='For Swagger debugging only',
    description='Quickly obtain a token for Swagger authentication',
)
async def login_swagger(
    db: CurrentSessionTransaction, obj: Annotated[HTTPBasicCredentials, Depends()]
) -> GetSwaggerToken:
    token, user = await auth_service.swagger_login(db=db, obj=obj)
    return GetSwaggerToken(access_token=token, user=user)  # type: ignore


@router.post(
    '/login',
    summary='User login',
    description='Log in using JSON; only supported in third-party API tools such as Postman',
    dependencies=[Depends(RateLimiter(Rate(5, Duration.MINUTE)))],
)
async def login(
    db: CurrentSessionTransaction,
    response: Response,
    obj: AuthLoginParam,
    background_tasks: BackgroundTasks,
) -> ResponseSchemaModel[GetLoginToken]:
    data = await auth_service.login(db=db, response=response, obj=obj, background_tasks=background_tasks)
    return response_base.success(data=data)


@router.get(
    '/codes',
    summary='Get all permission codes',
    description='Compatible with vben admin v5',
    dependencies=[DependsJwtAuth],
)
async def get_codes(db: CurrentSession, request: Request) -> ResponseSchemaModel[list[str]]:
    codes = await auth_service.get_codes(db=db, request=request)
    return response_base.success(data=codes)


@router.post('/refresh', summary='Refresh token')
async def refresh_token(db: CurrentSession, request: Request, response: Response) -> ResponseSchemaModel[GetNewToken]:
    data = await auth_service.refresh_token(db=db, request=request, response=response)
    return response_base.success(data=data)


@router.post('/logout', summary='User logout')
async def logout(request: Request, response: Response) -> ResponseModel:
    await auth_service.logout(request=request, response=response)
    return response_base.success()
