from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.schema import SchemaBase


class DictTypeSchemaBase(SchemaBase):
    """Dictionary type base schema"""

    name: str = Field(description='Dictionary name')
    code: str = Field(description='Dictionary code')
    remark: str | None = Field(None, description='Notes')


class CreateDictTypeParam(DictTypeSchemaBase):
    """Dictionary type creation parameters"""


class UpdateDictTypeParam(DictTypeSchemaBase):
    """Dictionary type update parameters"""


class DeleteDictTypeParam(SchemaBase):
    """Dictionary type deletion parameters"""

    pks: list[int] = Field(description='Dictionary type ID list')


class GetDictTypeDetail(DictTypeSchemaBase):
    """Dictionary type details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Dictionary type ID')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')
