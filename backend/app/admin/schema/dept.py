from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.enums import StatusType
from backend.common.schema import CustomEmailStr, CustomPhoneNumber, SchemaBase


class DeptSchemaBase(SchemaBase):
    """Department base schema"""

    name: str = Field(description='Department name')
    parent_id: int | None = Field(None, description='Parent department ID')
    sort: int = Field(0, ge=0, description='Sort order')
    leader: str | None = Field(None, description='Manager')
    phone: CustomPhoneNumber | None = Field(None, description='Contact phone number')
    email: CustomEmailStr | None = Field(None, description='Email')
    status: StatusType = Field(description='Status')


class CreateDeptParam(DeptSchemaBase):
    """Department creation parameters"""


class UpdateDeptParam(DeptSchemaBase):
    """Department update parameters"""


class GetDeptDetail(DeptSchemaBase):
    """Department details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Department ID')
    deleted: int = Field(description='Deleted (0: no, record ID: yes)')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')
    deleted_time: datetime | None = Field(None, description='Deletion time')


class GetDeptTree(GetDeptDetail):
    """Get department tree"""

    children: list['GetDeptTree'] | None = Field(None, description='Child menus')
