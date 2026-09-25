import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import DataClassBase, UniversalText, id_key


class CodeGenColumn(DataClassBase):
    """Code generation model column table"""

    __tablename__ = 'code_gen_column'
    __table_args__ = (
        sa.UniqueConstraint('code_gen_business_id', 'name', name='uk_code_gen_column_business_id_name'),
        {'comment': 'Code generation model column table'},
    )

    id: Mapped[id_key] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(sa.String(64), comment='Column name')
    comment: Mapped[str | None] = mapped_column(sa.String(256), default=None, comment='Column description')
    type: Mapped[str] = mapped_column(sa.String(32), default='String', comment='SQLAlchemy model column type')
    pd_type: Mapped[str] = mapped_column(
        sa.String(32), default='str', comment='Pydantic type corresponding to the column type'
    )
    default: Mapped[str | None] = mapped_column(UniversalText, default=None, comment='Column default value')
    sort: Mapped[int | None] = mapped_column(default=1, comment='Column sort order')
    length: Mapped[int] = mapped_column(default=0, comment='Column length')
    is_pk: Mapped[bool] = mapped_column(default=False, comment='Whether this is a primary key')
    is_nullable: Mapped[bool] = mapped_column(default=False, comment='Whether null values are allowed')

    # Logical foreign key
    code_gen_business_id: Mapped[int] = mapped_column(sa.BigInteger, default=0, comment='Code generation business ID')
