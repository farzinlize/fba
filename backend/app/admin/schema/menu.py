from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.enums import MenuType, StatusType
from backend.common.schema import SchemaBase


class MenuSchemaBase(SchemaBase):
    """Menu base schema"""

    title: str = Field(description='Menu title')
    name: str = Field(description='Menu name')
    path: str | None = Field(None, description='Route path')
    parent_id: int | None = Field(None, description='Parent menu ID')
    sort: int = Field(0, ge=0, description='Sort order')
    icon: str | None = Field(None, description='Icon')
    type: MenuType = Field(description='Menu type (0: directory, 1: menu, 2: button, 3: embedded, 4: external link)')
    component: str | None = Field(None, description='Component path')
    perms: str | None = Field(None, description='Permission identifier')
    status: StatusType = Field(description='Status')
    display: StatusType = Field(description='Visible')
    cache: StatusType = Field(description='Cached')
    link: str | None = Field(None, description='External URL')
    remark: str | None = Field(None, description='Notes')


class CreateMenuParam(MenuSchemaBase):
    """Menu creation parameters"""


class UpdateMenuParam(MenuSchemaBase):
    """Menu update parameters"""


class GetMenuDetail(MenuSchemaBase):
    """Menu details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Menu ID')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')


class GetMenuTree(GetMenuDetail):
    """Get menu tree"""

    children: list['GetMenuTree'] | None = Field(None, description='Child menus')
