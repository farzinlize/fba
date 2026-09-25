from datetime import datetime

from pydantic import ConfigDict, Field

from backend.app.admin.schema.data_scope import GetDataScopeWithRelationDetail
from backend.app.admin.schema.menu import GetMenuDetail
from backend.common.enums import StatusType
from backend.common.schema import SchemaBase


class RoleSchemaBase(SchemaBase):
    """Role base schema"""

    name: str = Field(description='Role name')
    status: StatusType = Field(description='Status')
    is_filter_scopes: bool = Field(True, description='Apply data permission filtering')
    remark: str | None = Field(None, description='Notes')


class CreateRoleParam(RoleSchemaBase):
    """Role creation parameters"""


class UpdateRoleParam(RoleSchemaBase):
    """Role update parameters"""


class DeleteRoleParam(SchemaBase):
    """Role deletion parameters"""

    pks: list[int] = Field(description='Role ID list')


class CreateRoleMenuParam(SchemaBase):
    """Role menu creation parameters"""

    role_id: int = Field(description='Role ID')
    menu_id: int = Field(description='Menu ID')


class UpdateRoleMenuParam(SchemaBase):
    """Role menu update parameters"""

    menus: list[int] = Field(description='Menu ID list')


class CreateRoleScopeParam(SchemaBase):
    """Role data scope creation parameters"""

    role_id: int = Field(description='Role ID')
    data_scope_id: int = Field(description='Data scope ID')


class UpdateRoleScopeParam(SchemaBase):
    """Role data scope update parameters"""

    scopes: list[int] = Field(description='Data scope ID list')


class GetRoleDetail(RoleSchemaBase):
    """Role details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Role ID')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')


class GetRoleWithRelationDetail(GetRoleDetail):
    """Role relationship details"""

    menus: list[GetMenuDetail | None] = Field([], description='Menu detail list')
    scopes: list[GetDataScopeWithRelationDetail | None] = Field([], description='Data scope list')
