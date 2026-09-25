from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, field_serializer

from backend.app.task import celery_app
from backend.common.schema import SchemaBase


class TaskResultSchemaBase(SchemaBase):
    """Task result base schema"""

    task_id: str = Field(description='Task ID')
    status: str = Field(description='Execution status')
    result: Any | None = Field(description='Execution result')
    date_done: datetime | None = Field(description='End time')
    traceback: str | None = Field(description='Error traceback')
    name: str | None = Field(description='Task name')
    args: bytes | None = Field(description='Task positional arguments')
    kwargs: bytes | None = Field(description='Task keyword arguments')
    worker: str | None = Field(description='Worker running the task')
    retries: int | None = Field(description='Retry count')
    queue: str | None = Field(description='Execution queue')


class DeleteTaskResultParam(SchemaBase):
    """Task result deletion parameters"""

    pks: list[int] = Field(description='Task result ID list')


class GetTaskResultDetail(TaskResultSchemaBase):
    """Task result details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Task result ID')

    @field_serializer('args', 'kwargs', when_used='unless-none')
    def serialize_params(self, value: bytes | None) -> Any:
        return celery_app.backend.decode(value)
