from datetime import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import DataClassBase, TimeZone, UniversalText, id_key
from backend.utils.timezone import timezone


class OperaLog(DataClassBase):
    """Operation log table"""

    __tablename__ = 'sys_opera_log'

    id: Mapped[id_key] = mapped_column(init=False)
    trace_id: Mapped[str] = mapped_column(sa.String(32), comment='Request trace ID')
    username: Mapped[str | None] = mapped_column(sa.String(64), comment='Username')
    method: Mapped[str] = mapped_column(sa.String(32), comment='Request method')
    title: Mapped[str] = mapped_column(sa.String(256), comment='Operation module')
    path: Mapped[str] = mapped_column(sa.String(512), comment='Request path')
    ip: Mapped[str] = mapped_column(sa.String(64), comment='IP address')
    country: Mapped[str | None] = mapped_column(sa.String(64), comment='Country')
    region: Mapped[str | None] = mapped_column(sa.String(64), comment='Region')
    city: Mapped[str | None] = mapped_column(sa.String(64), comment='City')
    user_agent: Mapped[str | None] = mapped_column(sa.String(512), comment='User agent')
    os: Mapped[str | None] = mapped_column(sa.String(64), comment='Operating system')
    browser: Mapped[str | None] = mapped_column(sa.String(64), comment='Browser')
    device: Mapped[str | None] = mapped_column(sa.String(64), comment='Device')
    args: Mapped[str | None] = mapped_column(sa.JSON(), comment='Request parameters')
    status: Mapped[int] = mapped_column(comment='Operation status (0: error, 1: normal)')
    code: Mapped[str] = mapped_column(sa.String(32), insert_default='200', comment='Operation status code')
    msg: Mapped[str | None] = mapped_column(UniversalText, comment='Message')
    cost_time: Mapped[float] = mapped_column(insert_default=0.0, comment='Request duration (ms)')
    opera_time: Mapped[datetime] = mapped_column(TimeZone, comment='Operation time')
    created_time: Mapped[datetime] = mapped_column(
        TimeZone, init=False, default_factory=timezone.now, comment='Creation time'
    )
