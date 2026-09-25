from typing import Any

from celery.schedules import schedule

from backend.app.task.utils.tzcrontab import TzAwareCrontab


def get_local_beat_schedule() -> dict[str, dict[str, Any]]:
    """Get local Celery beat task configuration"""
    # Reference: https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
    return {
        'Test synchronous task': {
            'task': 'task_demo',
            'schedule': schedule(30),
        },
        'Test asynchronous task': {
            'task': 'task_demo_async',
            'schedule': TzAwareCrontab('1'),
        },
        'Test task with arguments': {
            'task': 'task_demo_params',
            'schedule': TzAwareCrontab('1'),
            'args': ['Hello, '],
            'kwargs': {'world': 'world'},
        },
        'Clean up operation logs': {
            'task': 'backend.app.task.tasks.db_log.tasks.delete_db_opera_log',
            'schedule': TzAwareCrontab('0', '0', day_of_week='6'),
        },
        'Clean up login logs': {
            'task': 'backend.app.task.tasks.db_log.tasks.delete_db_login_log',
            'schedule': TzAwareCrontab('0', '0', day_of_month='15'),
        },
    }
