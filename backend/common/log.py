import inspect
import logging
import os
import re
import sys

from typing import Any

from loguru import logger

from backend.core.conf import settings
from backend.core.path_conf import LOG_DIR
from backend.utils.timezone import timezone
from backend.utils.trace_id import get_request_trace_id


class InterceptHandler(logging.Handler):
    """
    Log interception handler redirecting standard library logs to Loguru

    Reference: https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get the corresponding Loguru level, if available
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the caller that emitted the log message
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def default_formatter(record: dict) -> str:
    """
    Default log formatter

    :param record: Loguru Record object
    :return:
    """
    # Override SQLAlchemy echo output
    # https://github.com/sqlalchemy/sqlalchemy/discussions/12791
    record_name = record['name'] or ''
    if record_name.startswith('sqlalchemy'):
        record['message'] = re.sub(r'\s+', ' ', record['message']).strip()

    base_format = settings.LOG_FORMAT if settings.LOG_FORMAT.endswith('\n') else f'{settings.LOG_FORMAT}\n'
    if record.get('exception') is not None:
        base_format += '{exception}\n'

    return base_format


def request_id_filter(record: dict) -> bool:
    """
    Request ID filter

    :param record: Loguru Record object
    :return:
    """
    rid = get_request_trace_id()
    record['request_id'] = rid[: settings.TRACE_ID_LOG_LENGTH]
    return True


def setup_logging() -> None:
    """
    Configure log handlers

    Reference:
    - https://github.com/benoitc/gunicorn/issues/1572#issuecomment-638391953
    - https://github.com/pawamoy/pawamoy.github.io/issues/17
    """
    # Configure root log handler and level
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOG_STD_LEVEL)

    for name in logging.root.manager.loggerDict.keys():
        # Clear all default log handlers
        logging.getLogger(name).handlers = []

        # Configure log propagation rules
        if 'uvicorn.access' in name or 'watchfiles.main' in name:
            logging.getLogger(name).propagate = False
        else:
            logging.getLogger(name).propagate = True

        # Debug log handlers
        # logging.debug(f'{logging.getLogger(name)}, {logging.getLogger(name).propagate}')

    # Remove the default Loguru handler
    logger.remove()

    # Configure Loguru handlers
    logger.configure(
        handlers=[  # type: ignore[arg-type]
            {
                'sink': sys.stdout,
                'level': settings.LOG_STD_LEVEL,
                'format': default_formatter,
                'filter': lambda record: request_id_filter(record),
            }
        ]
    )


def set_custom_logfile() -> None:
    """Configure custom log files"""
    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)

    # Log file
    log_access_file = LOG_DIR / settings.LOG_ACCESS_FILENAME
    log_error_file = LOG_DIR / settings.LOG_ERROR_FILENAME

    # Log compression callback
    def compression(filepath: str) -> str:
        filename = filepath.split(os.sep)[-1]
        original_filename = filename.split('.')[0]
        if '-' in original_filename:
            return str(LOG_DIR / f'{original_filename}.log')
        return str(LOG_DIR / f'{original_filename}_{timezone.now().strftime("%Y-%m-%d")}.log')

    # Common log file configuration
    # https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add
    log_config: dict[str, Any] = {
        'format': default_formatter,
        'enqueue': True,
        'rotation': '00:00',
        'retention': '7 days',
        'compression': lambda filepath: os.rename(filepath, compression(filepath)),
    }

    # Standard output file
    logger.add(
        str(log_access_file),
        level=settings.LOG_FILE_ACCESS_LEVEL,
        filter=lambda record: record['level'].no <= 25,
        backtrace=False,
        diagnose=False,
        **log_config,
    )

    # Standard error file
    logger.add(
        str(log_error_file),
        level=settings.LOG_FILE_ERROR_LEVEL,
        filter=lambda record: record['level'].no >= 30,
        backtrace=True,
        diagnose=True,
        **log_config,
    )


# Create logger instance
log = logger
