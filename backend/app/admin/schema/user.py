from datetime import datetime
from typing import Annotated, Any

from pydantic import ConfigDict, Field, HttpUrl, PlainSerializer, model_validator
from typing_extensions import Self

from backend.app.admin.schema.dept import GetDeptDetail
from backend.app.admin.schema.role import GetRoleWithRelationDetail
from backend.common.enums import StatusType
from backend.common.schema import CustomEmailStr, CustomPhoneNumber, SchemaBase, ser_string


class AuthSchemaBase(SchemaBase):
    """User authentication base schema"""

    username: str = Field(description='Username')
    password: str = Field(description='Password')


class AuthLoginParam(AuthSchemaBase):
    """User login parameters"""

    uuid: str | None = Field(None, description='CAPTCHA UUID')
    captcha: str | None = Field(None, description='CAPTCHA')


class AddUserParam(AuthSchemaBase):
    """User creation parameters"""

    nickname: str | None = Field(None, description='Nickname')
    email: CustomEmailStr | None = Field(None, description='Email')
    phone: CustomPhoneNumber | None = Field(None, description='Mobile phone number')
    dept_id: int = Field(description='Department ID')
    roles: list[int] = Field(description='Role ID list')


class AddUserRoleParam(SchemaBase):
    """Add user roles"""

    user_id: int = Field(description='User ID')
    role_id: int = Field(description='Role ID')


class AddOAuth2UserParam(AuthSchemaBase):
    """OAuth2 user creation parameters"""

    password: str | None = Field(None, description='Password')
    nickname: str | None = Field(None, description='Nickname')
    email: CustomEmailStr | None = Field(None, description='Email')
    avatar: Annotated[HttpUrl, PlainSerializer(ser_string)] | None = Field(None, description='Avatar URL')


class ResetPasswordParam(SchemaBase):
    """Password reset parameters"""

    old_password: str = Field(description='Old password')
    new_password: str = Field(description='New password')
    confirm_password: str = Field(description='Confirm password')


class UserInfoSchemaBase(SchemaBase):
    """User information base schema"""

    dept_id: int | None = Field(None, description='Department ID')
    username: str = Field(description='Username')
    nickname: str = Field(description='Nickname')
    avatar: Annotated[HttpUrl, PlainSerializer(ser_string)] | None = Field(None, description='Avatar URL')
    email: CustomEmailStr | None = Field(None, description='Email')
    phone: CustomPhoneNumber | None = Field(None, description='Mobile number')


class UpdateUserParam(UserInfoSchemaBase):
    """User update parameters"""

    roles: list[int] = Field(description='Role ID list')


class GetUserInfoDetail(UserInfoSchemaBase):
    """User information details"""

    model_config = ConfigDict(from_attributes=True)

    dept_id: int | None = Field(None, description='Department ID')
    id: int = Field(description='User ID')
    uuid: str = Field(description='User UUID')
    status: StatusType = Field(description='Status')
    is_superuser: bool = Field(description='Whether the user is a superuser')
    is_staff: bool = Field(description='Whether the user is an administrator')
    is_multi_login: bool = Field(description='Whether concurrent logins are allowed')
    join_time: datetime = Field(description='Join time')
    last_login_time: datetime | None = Field(None, description='Last login time')


class GetUserInfoWithRelationDetail(GetUserInfoDetail):
    """User relationship details"""

    model_config = ConfigDict(from_attributes=True)

    dept: GetDeptDetail | None = Field(None, description='Department information')
    roles: list[GetRoleWithRelationDetail] = Field(description='Role list')


class GetCurrentUserInfoWithRelationDetail(GetUserInfoWithRelationDetail):
    """Current user relationship details"""

    model_config = ConfigDict(from_attributes=True)

    dept: str | None = Field(None, description='Department name')
    roles: list[str] = Field(description='Role name list')

    @model_validator(mode='before')
    @classmethod
    def handel(cls, data: Any) -> Self:
        """Process department and role data"""
        dept = data['dept']
        if dept:
            data['dept'] = dept['name']
        roles = data['roles']
        if roles:
            data['roles'] = [role['name'] for role in roles]
        return data
