import zoneinfo

from datetime import datetime
from datetime import timezone as datetime_timezone
from typing import Final

from backend.core.conf import settings

# Based on Wikipedia: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List
_UTC_IDENTIFIERS: Final = frozenset({
    'Etc/UCT',
    'Etc/Universal',
    'Etc/UTC',
    'Etc/Zulu',
    'UCT',
    'Universal',
    'UTC',
    'Zulu',
})


class TimeZone:
    def __init__(self) -> None:
        """Initialize timezone converter"""
        if settings.DATETIME_TIMEZONE in _UTC_IDENTIFIERS:
            self.tz_info = datetime_timezone.utc
        else:
            self.tz_info = zoneinfo.ZoneInfo(settings.DATETIME_TIMEZONE)

    def now(self) -> datetime:
        """Get current time in the configured timezone"""
        return datetime.now(self.tz_info)

    def from_datetime(self, t: datetime) -> datetime:
        """
        Convert datetime to the configured timezone

        :param t: Datetime object to convert
        :return:
        """
        return t.astimezone(self.tz_info)

    def from_str(self, t_str: str, format_str: str = settings.DATETIME_FORMAT) -> datetime:
        """
        Convert time string to datetime in the configured timezone

        :param t_str: Time string
        :param format_str: Time format string; defaults to settings.DATETIME_FORMAT
        :return:
        """
        return datetime.strptime(t_str, format_str).replace(tzinfo=self.tz_info)

    @staticmethod
    def to_str(t: datetime, format_str: str = settings.DATETIME_FORMAT) -> str:
        """
        Format datetime as a time string

        :param t: Datetime object
        :param format_str: Time format string; defaults to settings.DATETIME_FORMAT
        :return:
        """
        return t.strftime(format_str)

    @staticmethod
    def to_utc(t: datetime | int) -> datetime:
        """
        Convert datetime or timestamp to UTC

        :param t: Datetime object or timestamp to convert
        :return:
        """
        if isinstance(t, datetime):
            return t.astimezone(datetime_timezone.utc)
        return datetime.fromtimestamp(t, tz=datetime_timezone.utc)


timezone: TimeZone = TimeZone()
