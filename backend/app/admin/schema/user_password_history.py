from pydantic import Field

from backend.common.schema import SchemaBase


class UserPasswordHistorySchemaBase(SchemaBase):
    """User password history base schema"""

    user_id: int = Field(description='User ID')
    password: str = Field(description='Previous password')


class CreateUserPasswordHistoryParam(UserPasswordHistorySchemaBase):
    """Create user password history record"""
