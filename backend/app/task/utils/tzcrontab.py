from celery import schedules
from celery.schedules import ParseException

from backend.common.exception import errors
from backend.utils.timezone import timezone


class TzAwareCrontab(schedules.crontab):
    """Timezone-aware Crontab"""

    def __init__(self, minute='*', hour='*', day_of_week='*', day_of_month='*', month_of_year='*', app=None) -> None:  # ruff:ignore[missing-type-function-argument]
        super().__init__(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            nowfun=timezone.now,
            app=app,
        )


def crontab_verify(crontab: str) -> None:
    """
    Validate a standard crontab expression

    :param crontab: Standard crontab expression
    :return:
    """
    crontab_split = crontab.split(' ')
    if len(crontab_split) != 5:
        raise errors.RequestError(msg='Invalid Crontab expression')
    try:
        TzAwareCrontab.from_string(crontab)
    except (ParseException, ValueError):
        raise errors.RequestError(msg='Invalid Crontab expression')
