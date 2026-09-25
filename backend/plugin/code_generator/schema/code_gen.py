from pydantic import Field

from backend.common.schema import SchemaBase


class ImportParam(SchemaBase):
    """Import parameters"""

    app: str = Field(description='Application name identifying the app in which to generate code')
    table_schema: str = Field(description='Database name')
    table_name: str = Field(description='Database table name')
