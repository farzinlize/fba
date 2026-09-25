from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.enums import RoleDataRuleExpressionType, RoleDataRuleOperatorType
from backend.common.schema import SchemaBase


class DataRuleSchemaBase(SchemaBase):
    """Data rule base schema"""

    name: str = Field(description='Rule name')
    model: str = Field(description='Model name')
    column: str = Field(description='Field name')
    operator: RoleDataRuleOperatorType = Field(description='Operator (AND/OR)')
    expression: RoleDataRuleExpressionType = Field(description='Expression type')
    value: str = Field(description='Rule value')


class CreateDataRuleParam(DataRuleSchemaBase):
    """Data rule creation parameters"""


class UpdateDataRuleParam(DataRuleSchemaBase):
    """Data rule update parameters"""


class DeleteDataRuleParam(SchemaBase):
    """Data rule deletion parameters"""

    pks: list[int] = Field(description='Rule ID list')


class GetDataRuleDetail(DataRuleSchemaBase):
    """Data rule details"""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: int = Field(description='Rule ID')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')


class GetDataRuleColumnDetail(SchemaBase):
    """Available model field details for data rules"""

    key: str = Field(description='Field name')
    comment: str | None = Field(description='Field comment')


class GetDataRuleTemplateVariableDetail(SchemaBase):
    """Available template variable details for data rules"""

    key: str = Field(description='Variable identifier')
    comment: str = Field(description='Variable description')
