import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key


class DataScope(Base):
    """Data scope table"""

    __tablename__ = 'sys_data_scope'
    __table_args__ = (
        sa.UniqueConstraint('name', 'deleted', name='uk_sys_data_scope_name_deleted'),
        {'comment': 'Data scope table'},
    )

    id: Mapped[id_key] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(sa.String(64), comment='Name')
    status: Mapped[int] = mapped_column(default=1, comment='Status (0: disabled, 1: enabled)')
