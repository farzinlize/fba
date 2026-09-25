from celery import shared_task

from backend.app.admin.service.login_log_service import login_log_service
from backend.app.admin.service.opera_log_service import opera_log_service
from backend.database.db import async_db_session


@shared_task
async def delete_db_opera_log() -> str:
    """Automatically delete database operation logs"""
    async with async_db_session.begin() as db:
        await opera_log_service.delete_all(db=db)
        return 'Success'


@shared_task
async def delete_db_login_log() -> str:
    """Automatically delete database login logs"""
    async with async_db_session.begin() as db:
        await login_log_service.delete_all(db=db)
        return 'Success'
