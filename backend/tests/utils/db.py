from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio.session import AsyncSession

from backend.database.db import create_database_async_engine, create_database_async_session, get_database_url

# SQLAlchemy asynchronous engine and session
async_test_engine = create_database_async_engine(get_database_url(unittest=True))
async_test_db_session = create_database_async_session(async_test_engine)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_test_db_session() as session:
        yield session


async def override_get_db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_test_db_session.begin() as session:
        yield session
