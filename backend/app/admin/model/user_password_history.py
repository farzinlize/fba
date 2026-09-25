from datetime import datetime

import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import DataClassBase, TimeZone, id_key
from backend.utils.timezone import timezone


class UserPasswordHistory(DataClassBase):
    """User password history table"""

    __tablename__ = 'sys_user_password_history'

    id: Mapped[id_key] = mapped_column(init=False)
    user_id: Mapped[int] = mapped_column(sa.BigInteger, index=True, comment='User ID')
    password: Mapped[str] = mapped_column(sa.String(256), comment='Previous password')
    created_time: Mapped[datetime] = mapped_column(
        TimeZone,
        init=False,
        default_factory=timezone.now,
        comment='Creation time',
    )
