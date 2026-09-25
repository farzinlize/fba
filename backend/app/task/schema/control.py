from pydantic import Field

from backend.common.schema import SchemaBase


class GetTaskRegisteredDetail(SchemaBase):
    """Registered task details"""

    name: str = Field(description='Task name')
    task: str = Field(description='Task function')
