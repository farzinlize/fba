from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.conf import settings
from backend.plugin.core import check_plugin_installed
from backend.utils.serializers import select_list_serialize


def str_to_bool(value: str) -> bool:
    """Convert string to boolean"""
    return value == 'true'


async def load_config(
    db: AsyncSession,
    config_type_attr: str,
    mapping: dict[str, Callable[[str], object]],
    status_key: str,
) -> None:
    """
    Load configuration by type

    :param db: Database session
    :param config_type_attr: Configuration type attribute name
    :param mapping: Configuration mapping {config_key: converter}
    :param status_key: Status key
    :return:
    """
    if not check_plugin_installed('config'):
        return

    try:
        from backend.plugin.config.enums import ConfigType
        from backend.plugin.config.service.config_service import config_service
    except ImportError as e:
        raise ImportError('Failed to import configuration plugin utilities; contact the system administrator') from e

    config_type = getattr(ConfigType, config_type_attr)
    dynamic_config = await config_service.get_all(db=db, type=config_type)
    if not dynamic_config:
        return

    config_list = select_list_serialize(dynamic_config) if hasattr(dynamic_config[0], '__table__') else dynamic_config
    configs = {dc['key']: dc['value'] for dc in config_list}
    if configs.get(status_key, '1') == '0':
        return

    for config_key, converter in mapping.items():
        if config_key in configs:
            setattr(settings, config_key, converter(configs[config_key]))


async def load_user_security_config(db: AsyncSession) -> None:
    """
    Get user security configuration

    :param db: Database session
    :return:
    """
    mapping = {
        'USER_LOCK_THRESHOLD': int,
        'USER_LOCK_SECONDS': int,
        'USER_PASSWORD_EXPIRY_DAYS': int,
        'USER_PASSWORD_REMINDER_DAYS': int,
        'USER_PASSWORD_HISTORY_CHECK_COUNT': int,
        'USER_PASSWORD_MIN_LENGTH': int,
        'USER_PASSWORD_MAX_LENGTH': int,
        'USER_PASSWORD_REQUIRE_SPECIAL_CHAR': str_to_bool,
    }
    await load_config(db, 'user_security', mapping, 'USER_SECURITY_CONFIG_STATUS')


async def load_login_config(db: AsyncSession) -> None:
    """
    Get login configuration

    :param db: Database session
    :return:
    """
    mapping = {
        'LOGIN_CAPTCHA_ENABLED': str_to_bool,
    }
    await load_config(db, 'login', mapping, 'LOGIN_CONFIG_STATUS')
