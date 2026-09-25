from datetime import datetime

from pydantic import ConfigDict, Field
from pydantic.types import JsonValue

from backend.app.task.enums import PeriodType, TaskSchedulerType
from backend.common.enums import StatusType
from backend.common.schema import SchemaBase


class TaskSchedulerSchemaBase(SchemaBase):
    """Task schedule parameters"""

    name: str = Field(description='Task name')
    task: str = Field(description='Celery task to run')
    args: JsonValue | None = Field(None, description='Positional arguments accepted by the task')
    kwargs: JsonValue | None = Field(None, description='Keyword arguments accepted by the task')
    queue: str | None = Field(None, description='Queue defined in CELERY_TASK_QUEUES')
    exchange: str | None = Field(None, description='Exchange for low-level AMQP routing')
    routing_key: str | None = Field(None, description='Routing key for low-level AMQP routing')
    start_time: datetime | None = Field(None, description='Time at which the task starts triggering')
    expire_time: datetime | None = Field(None, description='Deadline after which the task stops triggering')
    expire_seconds: int | None = Field(
        None, description='Time interval in seconds after which the task stops triggering'
    )
    type: TaskSchedulerType = Field(description='Task schedule type (0: interval, 1: cron)')
    interval_every: int | None = Field(None, description='Number of periods between task runs')
    interval_period: PeriodType | None = Field(None, description='Type of period between task runs')
    crontab: str = Field(default='* * * * *', description='Crontab expression')
    one_off: bool = Field(default=False, description='Run only once')
    remark: str | None = Field(None, description='Notes')


class CreateTaskSchedulerParam(TaskSchedulerSchemaBase):
    """Task schedule creation parameters"""


class UpdateTaskSchedulerParam(TaskSchedulerSchemaBase):
    """Task schedule update parameters"""


class GetTaskSchedulerDetail(TaskSchedulerSchemaBase):
    """Task schedule details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Task schedule ID')
    status: StatusType = Field(description='Status')
    total_run_count: int = Field(description='Total run count')
    last_run_time: datetime | None = Field(None, description='Last run time')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')
