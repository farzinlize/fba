from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase
from backend.plugin.oauth2.enums import UserSocialType


class UserSocialSchemaBase(SchemaBase):
    """User social account base schema"""

    sid: str = Field(description='Third-party user ID')
    source: UserSocialType = Field(description='Social platform')


class CreateUserSocialParam(UserSocialSchemaBase):
    """User social account creation parameters"""

    user_id: int = Field(description='User ID')


class UpdateUserSocialParam(SchemaBase):
    """User social account update parameters"""


class GetUserSocialDetail(CreateUserSocialParam):
    """Get user social account details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='User social account ID')
