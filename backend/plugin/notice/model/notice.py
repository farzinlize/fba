import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, UniversalText, id_key


class Notice(Base):
    """System notice table"""

    __tablename__ = 'sys_notice'

    id: Mapped[id_key] = mapped_column(init=False)
    title: Mapped[str] = mapped_column(sa.String(64), comment='Title')
    type: Mapped[int] = mapped_column(comment='Type (0: notification, 1: announcement)')
    status: Mapped[int] = mapped_column(comment='Status (0: hidden, 1: visible)')
    content: Mapped[str] = mapped_column(UniversalText, comment='Content')
