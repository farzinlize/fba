import sqlalchemy as sa

from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base, id_key


class DataRule(Base):
    """Data rule table"""

    __tablename__ = 'sys_data_rule'
    __table_args__ = (
        sa.UniqueConstraint('name', 'deleted', name='uk_sys_data_rule_name_deleted'),
        {'comment': 'Data rule table'},
    )

    id: Mapped[id_key] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(sa.String(512), comment='Name')
    model: Mapped[str] = mapped_column(sa.String(64), comment='Model name')
    column: Mapped[str] = mapped_column(sa.String(32), comment='Model field name')
    operator: Mapped[int] = mapped_column(comment='Operator (0: AND, 1: OR)')
    expression: Mapped[int] = mapped_column(
        comment='Expression (0: ==, 1: !=, 2: >, 3: >=, 4: <, 5: <=, 6: in, 7: not_in)',
    )
    value: Mapped[str] = mapped_column(sa.String(256), comment='Rule value')
