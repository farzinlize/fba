import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key


class Dept(Base):
    """Department table"""

    __tablename__ = 'sys_dept'
    __table_args__ = (
        sa.UniqueConstraint('name', 'deleted', name='uk_sys_dept_name_deleted'),
        {'comment': 'Department table'},
    )

    id: Mapped[id_key] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(sa.String(64), comment='Department name')
    sort: Mapped[int] = mapped_column(default=0, comment='Sort order')
    leader: Mapped[str | None] = mapped_column(sa.String(32), default=None, comment='Manager')
    phone: Mapped[str | None] = mapped_column(sa.String(11), default=None, comment='Mobile phone')
    email: Mapped[str | None] = mapped_column(sa.String(64), default=None, comment='Email')
    status: Mapped[int] = mapped_column(default=1, comment='Department status (0: disabled, 1: enabled)')

    # Parent department
    parent_id: Mapped[int | None] = mapped_column(
        sa.BigInteger, default=None, index=True, comment='Parent department ID'
    )
