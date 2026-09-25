import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, UniversalText, id_key


class Config(Base):
    """Configuration parameter table"""

    __tablename__ = 'sys_config'
    __table_args__ = (
        sa.UniqueConstraint('key', 'deleted', name='uk_sys_config_key_deleted'),
        {'comment': 'Configuration parameter table'},
    )

    id: Mapped[id_key] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(sa.String(32), comment='Name')
    type: Mapped[str | None] = mapped_column(sa.String(32), server_default=None, comment='Type')
    key: Mapped[str] = mapped_column(sa.String(64), comment='Key')
    value: Mapped[str] = mapped_column(UniversalText, comment='Value')
    is_frontend: Mapped[bool] = mapped_column(default=False, comment='Whether this is a frontend parameter')
    remark: Mapped[str | None] = mapped_column(UniversalText, default=None, comment='Notes')
