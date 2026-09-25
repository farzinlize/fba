from datetime import datetime
from typing import Annotated

from sqlalchemy import BigInteger, DateTime, Text, TypeDecorator
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, declared_attr, mapped_column

from backend.common.enums import DataBaseType, PrimaryKeyType
from backend.core.conf import settings
from backend.utils.snowflake import snowflake
from backend.utils.timezone import timezone

# Generic Mapped primary key type; add it manually as shown below
# MappedBase -> id: Mapped[id_key]
# DataClassBase && Base -> id: Mapped[id_key] = mapped_column(init=False)
id_key = Annotated[
    int,
    mapped_column(
        BigInteger,
        primary_key=True,
        unique=True,
        index=True,
        autoincrement=True,
        sort_order=-999,
        comment='Primary key ID',
    )
    if PrimaryKeyType.autoincrement == settings.DATABASE_PK_MODE
    # Snowflake Mapped primary key type
    # Details: https://fastapi-practices.github.io/fastapi_best_architecture_docs/backend/reference/pk.html
    else mapped_column(
        BigInteger,
        primary_key=True,
        unique=True,
        index=True,
        default=snowflake.generate,
        sort_order=-999,
        comment='Snowflake primary key ID',
    ),
]


class UniversalText(TypeDecorator[str]):
    """PostgreSQL- and MySQL-compatible long text type"""

    impl = LONGTEXT if DataBaseType.mysql == settings.DATABASE_TYPE else Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:  # ruff:ignore[missing-type-function-argument]
        return value

    def process_result_value(self, value: str | None, dialect) -> str | None:  # ruff:ignore[missing-type-function-argument]
        return value


class TimeZone(TypeDecorator[datetime]):
    """PostgreSQL- and MySQL-compatible timezone-aware type"""

    impl = DateTime(timezone=True)
    cache_ok = True

    @property
    def python_type(self) -> type[datetime]:
        return datetime

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:  # ruff:ignore[missing-type-function-argument]
        if value is not None and value.utcoffset() != timezone.now().utcoffset():
            # TODO: Handle daylight saving time offsets
            value = timezone.from_datetime(value)
        return value

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:  # ruff:ignore[missing-type-function-argument]
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.tz_info)
        return value


# Mixin: an object-oriented programming concept that clarifies structure; `Wiki <https://en.wikipedia.org/wiki/Mixin/>`__
class UserMixin(MappedAsDataclass):
    """User mixin data class"""

    created_by: Mapped[int] = mapped_column(sort_order=998, comment='Created by')
    updated_by: Mapped[int | None] = mapped_column(init=False, default=None, sort_order=998, comment='Updated by')


class DateTimeMixin(MappedAsDataclass):
    """Date/time mixin data class"""

    created_time: Mapped[datetime] = mapped_column(
        TimeZone,
        init=False,
        default_factory=timezone.now,
        sort_order=999,
        comment='Creation time',
    )
    updated_time: Mapped[datetime | None] = mapped_column(
        TimeZone,
        init=False,
        onupdate=timezone.now,
        sort_order=999,
        comment='Update time',
    )


class LogicalDeleteMixin(MappedAsDataclass):
    """Soft deletion mixin data class"""

    deleted: Mapped[int] = mapped_column(
        BigInteger,
        init=False,
        default=0,
        server_default='0',
        sort_order=999,
        comment='Deleted (0: no, record ID: yes)',
    )
    deleted_time: Mapped[datetime | None] = mapped_column(
        TimeZone,
        init=False,
        default=None,
        sort_order=999,
        comment='Deletion time',
    )


class MappedBase(AsyncAttrs, DeclarativeBase):
    """
    Declarative base class for all base classes and data models

    `AsyncAttrs <https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncAttrs>`__

    `DeclarativeBase <https://docs.sqlalchemy.org/en/20/orm/declarative_config.html>`__

    `mapped_column() <https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.mapped_column>`__
    """

    @declared_attr.directive
    def __tablename__(self) -> str:
        """Generate table name"""
        return self.__name__.lower()

    @declared_attr.directive
    def __table_args__(self) -> dict:
        """Table configuration"""
        return {'comment': self.__doc__ or ''}


class DataClassBase(MappedAsDataclass, MappedBase):
    """
    Declarative base with dataclass integration for advanced configuration.
    Take care with its behavior, especially alongside DeclarativeBase.

    `MappedAsDataclass <https://docs.sqlalchemy.org/en/20/orm/dataclasses.html#orm-declarative-native-dataclasses>`__
    """

    __abstract__ = True


class Base(DataClassBase, DateTimeMixin, LogicalDeleteMixin):
    """
    Declarative base with dataclass integration and common mixin table fields
    """

    __abstract__ = True
