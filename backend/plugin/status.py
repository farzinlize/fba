import json

from typing import cast

from fastapi import Request

from backend.common.enums import StatusType
from backend.common.exception import errors
from backend.common.log import log
from backend.core.conf import settings
from backend.database.redis import redis_client
from backend.plugin.errors import PluginInjectError


async def repair_plugin_cache(plugin: str) -> str:
    """
    Restore missing plugin status cache

    :param plugin: Plugin name
    :return:
    """
    from backend.plugin.core import load_plugin_config
    from backend.plugin.validator import validate_plugin_config

    plugin_config = load_plugin_config(plugin)
    validate_plugin_config(plugin, plugin_config)
    plugin_config['plugin']['name'] = plugin
    plugin_config['plugin']['enable'] = str(StatusType.enable.value)
    plugin_info = json.dumps(plugin_config, ensure_ascii=False)
    await redis_client.set(f'{settings.PLUGIN_REDIS_PREFIX}:{plugin}', plugin_info)
    return plugin_info


def get_plugin_enable(plugin_info: str | None, default_status: int) -> str:
    """
    Parse plugin enabled status

    :param plugin_info: Cached plugin information
    :param default_status: Default status value
    :return:
    """
    if not plugin_info:
        return str(default_status)

    try:
        return json.loads(plugin_info)['plugin']['enable']
    except Exception:
        return str(default_status)


class PluginStatusChecker:
    """Plugin status checker"""

    def __init__(self, plugin: str) -> None:
        """
        Initialize plugin status checker

        :param plugin: Plugin name
        :return:
        """
        self.plugin = plugin

    async def __call__(self, request: Request) -> None:
        """
        Validate plugin status

        :param request: FastAPI request object
        :return:
        """
        plugin_info = cast(
            'str | None',
            await redis_client.get(f'{settings.PLUGIN_REDIS_PREFIX}:{self.plugin}'),
        )
        if not plugin_info:
            log.warning('Plugin {} status is uninitialized or missing; attempting automatic recovery', self.plugin)
            try:
                plugin_info = await repair_plugin_cache(self.plugin)
            except Exception as e:
                log.exception('Automatic status recovery failed for plugin {}', self.plugin)
                raise PluginInjectError(
                    'Plugin status is uninitialized or missing; contact the system administrator'
                ) from e

        if get_plugin_enable(plugin_info, StatusType.disable.value) != str(StatusType.enable.value):
            raise errors.ServerError(msg=f'Plugin {self.plugin} is disabled; contact the system administrator')
