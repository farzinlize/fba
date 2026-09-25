from datetime import datetime

from pydantic import ConfigDict, Field

from backend.app.admin.schema.data_rule import GetDataRuleDetail
from backend.common.enums import StatusType
from backend.common.schema import SchemaBase


class DataScopeSchemaBase(SchemaBase):
    """Data scope base schema"""

    name: str = Field(description='Name')
    status: StatusType = Field(description='Status')


class CreateDataScopeParam(DataScopeSchemaBase):
    """Data scope creation parameters"""


class UpdateDataScopeParam(DataScopeSchemaBase):
    """Data scope update parameters"""


class CreateDataScopeRuleParam(SchemaBase):
    """Data scope rule creation parameters"""

    data_scope_id: int = Field(description='Data scope ID')
    data_rule_id: int = Field(description='Data rule ID')


class UpdateDataScopeRuleParam(SchemaBase):
    """Data scope rule update parameters"""

    rules: list[int] = Field(description='Data rule ID list')


class DeleteDataScopeParam(SchemaBase):
    """Data scope deletion parameters"""

    pks: list[int] = Field(description='Data scope ID list')


class GetDataScopeDetail(DataScopeSchemaBase):
    """Data scope details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Data scope ID')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')


class GetDataScopeWithRelationDetail(GetDataScopeDetail):
    """Data scope relationship details"""

    rules: list[GetDataRuleDetail | None] = Field([], description='Data rule list')
