import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, UniversalText, id_key


class DictType(Base):
    """Dictionary type table"""

    __tablename__ = 'sys_dict_type'
    __table_args__ = (
        sa.UniqueConstraint('code', 'deleted', name='uk_sys_dict_type_code_deleted'),
        {'comment': 'Dictionary type table'},
    )

    id: Mapped[id_key] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(sa.String(32), comment='Dictionary type name')
    code: Mapped[str] = mapped_column(sa.String(32), comment='Dictionary type code')
    remark: Mapped[str | None] = mapped_column(UniversalText, default=None, comment='Notes')
