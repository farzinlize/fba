import sys

from collections.abc import AsyncGenerator, Mapping
from contextlib import AbstractAsyncContextManager
from functools import partial
from typing import Annotated, Any, TypeAlias
from uuid import uuid4

from fastapi import Depends
from sqlalchemy import URL, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.common.enums import DataBaseType
from backend.common.log import log
from backend.common.model import MappedBase
from backend.common.observability.prometheus.sqlalchemy import observe_sqlalchemy_pool_connections
from backend.core.conf import settings


def get_database_url(*, unittest: bool = False, with_database: bool = True) -> URL:
    """
    Create database URL

    :param unittest: Whether this is for unit tests
    :param with_database: Whether to include the database name (not needed when creating the database)
    :return:
    """
    if with_database:
        database = settings.DATABASE_SCHEMA if not unittest else f'{settings.DATABASE_SCHEMA}_test'
    else:
        database = None if DataBaseType.mysql == settings.DATABASE_TYPE else 'postgres'

    url = URL.create(
        drivername='mysql+asyncmy' if DataBaseType.mysql == settings.DATABASE_TYPE else 'postgresql+asyncpg',
        username=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=database,
    )
    if DataBaseType.mysql == settings.DATABASE_TYPE and with_database:
        url = url.update_query_dict({'charset': settings.DATABASE_CHARSET})
    return url


def create_database_async_engine(url: str | URL) -> AsyncEngine:
    """
    Create asynchronous database engine

    :param url: Database connection URL
    :return:
    """
    try:
        return create_async_engine(
            url,
            echo=settings.DATABASE_ECHO,
            echo_pool=settings.DATABASE_POOL_ECHO,
            future=True,
            # Moderate concurrency
            pool_size=10,  # Low: - High: +
            max_overflow=20,  # Low: - High: +
            pool_timeout=30,  # Low: + High: -
            pool_recycle=3600,  # Low: + High: -
            pool_pre_ping=True,  # Low: False High: True
            pool_use_lifo=False,  # Low: False High: True
        )
    except Exception as e:
        log.error(f'Database connection failed: {e}')
        sys.exit()


class DatabaseAsyncSessionMaker:
    """Select the corresponding async_sessionmaker by data source name"""

    def __init__(self, makers: Mapping[str, async_sessionmaker[AsyncSession]]) -> None:
        if 'default' not in makers:
            raise ValueError('Session factories must include the default data source')
        self._makers = dict(makers)

    def _get_maker(self, source: str) -> async_sessionmaker[AsyncSession]:
        """
        Get the session factory for a data source

        :param source: Data source name
        :return:
        """
        try:
            return self._makers[source]
        except KeyError as e:
            raise ValueError(f'Unknown database data source: {source}') from e

    def __call__(self, source: str = 'default', **kwargs: Any) -> AsyncSession:
        """
        Create database session

        :param source: Data source name
        :return:
        """
        return self._get_maker(source)(**kwargs)

    def begin(self, source: str = 'default') -> AbstractAsyncContextManager[AsyncSession]:
        """
        Create a session and begin a transaction; commit and close on exit

        :param source: Data source name
        :return:
        """
        return self._get_maker(source).begin()


def create_database_async_session(
    async_engine: AsyncEngine,
    *,
    source_binds: Mapping[str, AsyncEngine] | None = None,
) -> DatabaseAsyncSessionMaker:
    """
    Create asynchronous database sessions supporting named data sources

    :param async_engine: Default data source asynchronous engine
    :param source_binds: Additional data source asynchronous engines
    :return:
    """
    engines = dict(source_binds or {})
    engines.setdefault('default', async_engine)
    return DatabaseAsyncSessionMaker({
        source: async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        for source, engine in engines.items()
    })


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get default data source session"""
    async with async_db_session() as session:
        yield session


async def get_db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """Get default data source transactional session"""
    async with async_db_session.begin() as session:
        yield session


async def create_tables() -> None:
    """Create database tables"""
    async with async_engine.begin() as coon:
        await coon.run_sync(MappedBase.metadata.create_all)


async def drop_tables() -> None:
    """Drop database tables"""
    async with async_engine.begin() as conn:
        await conn.run_sync(MappedBase.metadata.drop_all)


def uuid4_str() -> str:
    """Database engine UUID type compatibility workaround"""
    return str(uuid4())


# SQLAlchemy asynchronous engines and sessions
async_engine = create_database_async_engine(get_database_url())
_database_engines: dict[str, AsyncEngine] = {'default': async_engine}
for source, url in settings.DATABASE_SOURCES.items():
    if not source or source == 'default':
        raise ValueError('DATABASE_SOURCES names must not be empty or equal to default')
    _database_engines[source] = create_database_async_engine(url)

async_db_session = create_database_async_session(async_engine, source_binds=_database_engines)


def get_database_engines() -> Mapping[str, AsyncEngine]:
    """Get all database engines"""
    return _database_engines


async def dispose_database() -> None:
    """Dispose of all database connection pools"""
    for engine in _database_engines.values():
        await engine.dispose()


# Monitor SQLAlchemy connection pool metrics
for source, engine in _database_engines.items():
    event.listen(
        engine.sync_engine.pool,
        'connect',
        partial(observe_sqlalchemy_pool_connections, pool=engine.sync_engine.pool, source=source),
    )
    event.listen(
        engine.sync_engine.pool,
        'checkout',
        partial(observe_sqlalchemy_pool_connections, pool=engine.sync_engine.pool, source=source),
    )
    event.listen(
        engine.sync_engine.pool,
        'checkin',
        partial(observe_sqlalchemy_pool_connections, pool=engine.sync_engine.pool, source=source),
    )

# Session Annotated
CurrentSession: TypeAlias = Annotated[AsyncSession, Depends(get_db)]
CurrentSessionTransaction: TypeAlias = Annotated[AsyncSession, Depends(get_db_transaction)]
