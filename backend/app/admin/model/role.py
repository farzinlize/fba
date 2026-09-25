import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, UniversalText, id_key


class Role(Base):
    """Role table"""

    __tablename__ = 'sys_role'
    __table_args__ = (
        sa.UniqueConstraint('name', 'deleted', name='uk_sys_role_name_deleted'),
        {'comment': 'Role table'},
    )

    id: Mapped[id_key] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(sa.String(32), comment='Role name')
    status: Mapped[int] = mapped_column(default=1, comment='Role status (0: disabled, 1: enabled)')
    is_filter_scopes: Mapped[bool] = mapped_column(
        default=True, comment='Apply data permission filtering (0: no, 1: yes)'
    )
    remark: Mapped[str | None] = mapped_column(UniversalText, default=None, comment='Notes')
