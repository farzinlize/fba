import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, UniversalText, id_key


class CodeGenBusiness(Base):
    """Code generation business table"""

    __tablename__ = 'code_gen_business'
    __table_args__ = (
        sa.UniqueConstraint('table_name', 'deleted', name='uk_code_gen_business_table_name_deleted'),
        {'comment': 'Code generation business table'},
    )

    id: Mapped[id_key] = mapped_column(init=False)
    app_name: Mapped[str] = mapped_column(sa.String(64), comment='Application name')
    table_name: Mapped[str] = mapped_column(sa.String(256), comment='Table name')
    doc_comment: Mapped[str] = mapped_column(sa.String(256), comment='Documentation comment')
    table_comment: Mapped[str | None] = mapped_column(sa.String(256), default=None, comment='Table description')
    class_name: Mapped[str | None] = mapped_column(sa.String(64), default=None, comment='Base class name')
    schema_name: Mapped[str | None] = mapped_column(sa.String(64), default=None, comment='Schema name')
    filename: Mapped[str | None] = mapped_column(sa.String(64), default=None, comment='Base filename')
    datetime_mixin: Mapped[bool] = mapped_column(default=True, comment='Whether to include time mixin columns')
    api_version: Mapped[str] = mapped_column(sa.String(32), default='v1', comment='API version')
    tag: Mapped[str | None] = mapped_column(sa.String(64), default=None, comment='API tags')
    gen_path: Mapped[str | None] = mapped_column(sa.String(256), default=None, comment='Output path')
    remark: Mapped[str | None] = mapped_column(UniversalText, default=None, comment='Notes')
