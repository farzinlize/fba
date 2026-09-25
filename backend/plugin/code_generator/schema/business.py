from datetime import datetime

from pydantic import ConfigDict, Field, field_validator

from backend.common.exception import errors
from backend.common.schema import SchemaBase
from backend.utils.pattern_validate import is_english_identifier


class CodeGenBusinessSchemaBase(SchemaBase):
    """Code generation business base schema"""

    app_name: str = Field(description='Application name (English)')
    table_name: str = Field(description='Table name (English)')
    doc_comment: str = Field(description='Documentation comment (for function and parameter documentation)')
    table_comment: str | None = Field(None, description='Table description')
    class_name: str | None = Field(None, description='Base class name for Python code')
    schema_name: str | None = Field(None, description='Base class name for Python schema code')
    filename: str | None = Field(None, description='Base filename for Python code')
    datetime_mixin: bool = Field(True, description='Whether to include time mixin columns')
    api_version: str = Field('v1', description='API version')
    tag: str | None = Field(None, description='API tags (for route grouping)')
    gen_path: str | None = Field(None, description='Output path (defaults to backend/app)')
    remark: str | None = Field(None, description='Notes')

    @field_validator('app_name', 'table_name')
    @classmethod
    def validate_english_only(cls, v: str) -> str:
        """Validate English fields"""
        if not is_english_identifier(v):
            raise errors.RequestError(
                msg='Must start with an English letter and contain only English letters and underscores'
            )
        return v


class CreateCodeGenBusinessParam(CodeGenBusinessSchemaBase):
    """Code generation business creation parameters"""


class UpdateCodeGenBusinessParam(CodeGenBusinessSchemaBase):
    """Code generation business update parameters"""


class GetCodeGenBusinessDetail(CodeGenBusinessSchemaBase):
    """Get code generation business details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Primary key ID')
    created_time: datetime = Field(description='Creation time')
    updated_time: datetime | None = Field(None, description='Update time')
