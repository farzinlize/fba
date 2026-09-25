from datetime import datetime

from pydantic import Field

from backend.app.admin.schema.user import GetUserInfoDetail
from backend.common.enums import StatusType
from backend.common.schema import SchemaBase


class GetSwaggerToken(SchemaBase):
    """Swagger authentication token"""

    access_token: str = Field(description='Access token')
    token_type: str = Field('Bearer', description='Token type')
    user: GetUserInfoDetail = Field(description='User information')


class AccessTokenBase(SchemaBase):
    """Access token base schema"""

    access_token: str = Field(description='Access token')
    access_token_expire_time: datetime = Field(description='Token expiration time')
    session_uuid: str = Field(description='Session UUID')


class GetNewToken(AccessTokenBase):
    """Get new token"""


class GetLoginToken(AccessTokenBase):
    """Get login token"""

    password_expire_days_remaining: int | None = Field(None, description='Days remaining until password expiration')
    user: GetUserInfoDetail = Field(description='User information')


class GetTokenDetail(SchemaBase):
    """Token details"""

    id: int = Field(description='User ID')
    session_uuid: str = Field(description='Session UUID')
    username: str = Field(description='Username')
    nickname: str = Field(description='Nickname')
    ip: str = Field(description='IP address')
    os: str = Field(description='Operating system')
    browser: str = Field(description='Browser')
    device: str = Field(description='Device')
    status: StatusType = Field(description='Status')
    last_login_time: str = Field(description='Last login time')
    expire_time: datetime = Field(description='Expiration time')
