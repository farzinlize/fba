import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, UniversalText, id_key


class Menu(Base):
    """Menu table"""

    __tablename__ = 'sys_menu'

    id: Mapped[id_key] = mapped_column(init=False)
    title: Mapped[str] = mapped_column(sa.String(64), comment='Menu title')
    name: Mapped[str] = mapped_column(sa.String(64), comment='Menu name')
    path: Mapped[str | None] = mapped_column(sa.String(200), comment='Route path')
    sort: Mapped[int] = mapped_column(default=0, comment='Sort order')
    icon: Mapped[str | None] = mapped_column(sa.String(128), default=None, comment='Menu icon')
    type: Mapped[int] = mapped_column(
        default=0, comment='Menu type (0: directory, 1: menu, 2: button, 3: embedded, 4: external link)'
    )
    component: Mapped[str | None] = mapped_column(sa.String(256), default=None, comment='Component path')
    perms: Mapped[str | None] = mapped_column(sa.String(128), default=None, comment='Permission identifier')
    status: Mapped[int] = mapped_column(default=1, comment='Menu status (0: disabled, 1: enabled)')
    display: Mapped[int] = mapped_column(default=1, comment='Visible (0: no, 1: yes)')
    cache: Mapped[int] = mapped_column(default=1, comment='Cached (0: no, 1: yes)')
    link: Mapped[str | None] = mapped_column(UniversalText, default=None, comment='External URL')
    remark: Mapped[str | None] = mapped_column(UniversalText, default=None, comment='Notes')

    # Parent menu
    parent_id: Mapped[int | None] = mapped_column(sa.BigInteger, default=None, index=True, comment='Parent menu ID')
