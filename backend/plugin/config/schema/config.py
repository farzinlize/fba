from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class ConfigSchemaBase(SchemaBase):
    """Configuration parameter base schema"""

    name: str = Field(description='Configuration parameter name')
    type: str | None = Field(None, description='Configuration parameter type')
    key: str = Field(description='Configuration parameter key')
    value: str = Field(description='Configuration parameter value')
    is_frontend: bool = Field(description='Whether this configuration parameter is for the frontend')
    remark: str | None = Field(None, description='Notes')


class CreateConfigParam(ConfigSchemaBase):
    """Configuration parameter creation parameters"""


class UpdateConfigParam(ConfigSchemaBase):
    """Configuration parameter update parameters"""


class UpdateConfigsParam(UpdateConfigParam):
    """Bulk configuration parameter update parameters"""

    id: int = Field(description='Configuration parameter ID')


class GetConfigDetail(ConfigSchemaBase):
    """Configuration parameter details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Configuration parameter ID')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')
