from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.enums import StatusType
from backend.common.schema import SchemaBase


class DictDataSchemaBase(SchemaBase):
    """Dictionary entry base schema"""

    type_id: int = Field(description='Dictionary type ID')
    label: str = Field(description='Dictionary label')
    value: str = Field(description='Dictionary value')
    color: str | None = Field(None, description='Label color')
    sort: int = Field(description='Sort order')
    status: StatusType = Field(description='Status')
    remark: str | None = Field(None, description='Notes')


class CreateDictDataParam(DictDataSchemaBase):
    """Dictionary entry creation parameters"""


class UpdateDictDataParam(DictDataSchemaBase):
    """Dictionary entry update parameters"""


class DeleteDictDataParam(SchemaBase):
    """Dictionary entry deletion parameters"""

    pks: list[int] = Field(description='Dictionary entry ID list')


class GetDictDataDetail(DictDataSchemaBase):
    """Dictionary entry details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Dictionary entry ID')
    type_code: str = Field(description='Dictionary type code')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')
