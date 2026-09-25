import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key


class UserSocial(Base):
    """User social account table (OAuth2)"""

    __tablename__ = 'sys_user_social'
    __table_args__ = (
        sa.UniqueConstraint('user_id', 'source', 'deleted', name='uk_sys_user_social_user_id_source_deleted'),
        sa.UniqueConstraint('sid', 'source', 'deleted', name='uk_sys_user_social_sid_source_deleted'),
        {'comment': 'User social account table (OAuth2)'},
    )

    id: Mapped[id_key] = mapped_column(init=False)
    sid: Mapped[str] = mapped_column(sa.String(256), comment='Third-party user ID')
    source: Mapped[str] = mapped_column(sa.String(32), comment='Third-party user provider')

    # Logical foreign key
    user_id: Mapped[int] = mapped_column(sa.BigInteger, comment='Related user ID')
