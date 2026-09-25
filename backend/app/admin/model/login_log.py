from datetime import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import DataClassBase, TimeZone, UniversalText, id_key
from backend.utils.timezone import timezone


class LoginLog(DataClassBase):
    """Login log table"""

    __tablename__ = 'sys_login_log'

    id: Mapped[id_key] = mapped_column(init=False)
    user_uuid: Mapped[str] = mapped_column(sa.String(64), comment='User UUID')
    username: Mapped[str] = mapped_column(sa.String(64), comment='Username')
    status: Mapped[int] = mapped_column(insert_default=0, comment='Login status (0: failed, 1: successful)')
    ip: Mapped[str] = mapped_column(sa.String(64), comment='Login IP address')
    country: Mapped[str | None] = mapped_column(sa.String(64), comment='Country')
    region: Mapped[str | None] = mapped_column(sa.String(64), comment='Region')
    city: Mapped[str | None] = mapped_column(sa.String(64), comment='City')
    user_agent: Mapped[str | None] = mapped_column(sa.String(512), comment='Request headers')
    os: Mapped[str | None] = mapped_column(sa.String(64), comment='Operating system')
    browser: Mapped[str | None] = mapped_column(sa.String(64), comment='Browser')
    device: Mapped[str | None] = mapped_column(sa.String(64), comment='Device')
    msg: Mapped[str] = mapped_column(UniversalText, comment='Message')
    login_time: Mapped[datetime] = mapped_column(TimeZone, comment='Login time')
    created_time: Mapped[datetime] = mapped_column(
        TimeZone,
        init=False,
        default_factory=timezone.now,
        comment='Creation time',
    )
