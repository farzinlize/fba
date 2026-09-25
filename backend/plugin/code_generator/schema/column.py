from pydantic import ConfigDict, Field, field_validator

from backend.common.schema import SchemaBase
from backend.plugin.code_generator.utils.type_conversion import sql_type_to_sqlalchemy


class CodeGenColumnSchemaBase(SchemaBase):
    """Code generation model base schema"""

    name: str = Field(description='Column name')
    comment: str | None = Field(None, description='Column description')
    type: str = Field(description='SQLAlchemy model column type')
    default: str | None = Field(None, description='Column default value')
    sort: int = Field(description='Column sort order')
    length: int = Field(description='Column length')
    is_pk: bool = Field(False, description='Whether this is a primary key')
    is_nullable: bool = Field(False, description='Whether null values are allowed')
    code_gen_business_id: int = Field(description='Code generation business ID')

    @field_validator('type')
    @classmethod
    def normalize_type(cls, v: str) -> str:
        """Normalize type"""
        return sql_type_to_sqlalchemy(v)


class CreateCodeGenColumnParam(CodeGenColumnSchemaBase):
    """Code generation model column creation parameters"""


class CreateCodeGenColumnInternalParam(CreateCodeGenColumnParam):
    """Internal code generation model column creation parameters"""

    pd_type: str | None = Field(None, description='Pydantic type corresponding to the column type')


class UpdateCodeGenColumnParam(CodeGenColumnSchemaBase):
    """Code generation model column update parameters"""


class GetCodeGenColumnDetail(CodeGenColumnSchemaBase):
    """Get code generation model column details"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Primary key ID')
    pd_type: str = Field(description='Pydantic type corresponding to the column type')
