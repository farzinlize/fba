from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class LoginLogSchemaBase(SchemaBase):
    """Login log base schema"""

    user_uuid: str = Field(description='User UUID')
    username: str = Field(description='Username')
    status: int = Field(description='Login status')
    ip: str = Field(description='IP address')
    country: str | None = Field(None, description='Country')
    region: str | None = Field(None, description='Region')
    city: str | None = Field(None, description='City')
    user_agent: str | None = Field(description='User agent')
    browser: str | None = Field(None, description='Browser')
    os: str | None = Field(None, description='Operating system')
    device: str | None = Field(None, description='Device')
    msg: str = Field(description='Message')
    login_time: datetime = Field(description='Login time')


class CreateLoginLogParam(LoginLogSchemaBase):
    """Login log creation parameters"""


class UpdateLoginLogParam(LoginLogSchemaBase):
    """Login log update parameters"""


class DeleteLoginLogParam(SchemaBase):
    """Login log deletion parameters"""

    pks: list[int] = Field(description='Login log ID list')


class GetLoginLogDetail(LoginLogSchemaBase):
    """Login log details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Log ID')
    created_time: datetime = Field(description='Creation time')
