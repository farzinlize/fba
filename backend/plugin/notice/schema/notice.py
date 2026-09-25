from datetime import datetime

from pydantic import ConfigDict, Field

from backend.common.enums import StatusType
from backend.common.schema import SchemaBase
from backend.plugin.notice.enums import NoticeType


class NoticeSchemaBase(SchemaBase):
    """Notice base schema"""

    title: str = Field(description='Title')
    type: NoticeType = Field(description='Type (0: notification, 1: announcement)')
    status: StatusType = Field(description='Status (0: hidden, 1: visible)')
    content: str = Field(description='Content')


class CreateNoticeParam(NoticeSchemaBase):
    """Notice creation parameters"""


class UpdateNoticeParam(NoticeSchemaBase):
    """Notice update parameters"""


class DeleteNoticeParam(SchemaBase):
    """Notice deletion parameters"""

    pks: list[int] = Field(description='Notice ID list')


class GetNoticeDetail(NoticeSchemaBase):
    """Notice details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Notice ID')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')
