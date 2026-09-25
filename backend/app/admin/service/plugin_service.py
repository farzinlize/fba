import io
import json

from typing import Any

import anyio

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from backend.common.enums import PluginType, StatusType
from backend.common.exception import errors
from backend.core.conf import settings
from backend.core.path_conf import PLUGIN_DIR
from backend.database.redis import redis_client
from backend.plugin.core import get_required_plugins
from backend.plugin.installer import install_git_plugin, install_zip_plugin, remove_plugin, zip_plugin
from backend.plugin.requirements import uninstall_requirements_async
from backend.utils.timezone import timezone


class PluginService:
    """Plugin service"""

    @staticmethod
    async def get_all() -> list[dict[str, Any]]:
        """Get all plugins"""

        changed_key = f'{settings.PLUGIN_REDIS_PREFIX}:changed'
        keys = [key for key in await redis_client.get_by_prefix(settings.PLUGIN_REDIS_PREFIX) if key != changed_key]
        if not keys:
            return []

        result = []
        plugin_infos = await redis_client.mget(*keys)
        for info in plugin_infos:
            if info is None:
                continue

            plugin_info = json.loads(info)
            if isinstance(plugin_info, dict):
                result.append(plugin_info)

        return result

    @staticmethod
    async def changed() -> str | None:
        """Check whether plugins have changed"""
        return await redis_client.get(f'{settings.PLUGIN_REDIS_PREFIX}:changed')

    @staticmethod
    async def install(*, type: PluginType, file: UploadFile | None = None, repo_url: str | None = None) -> str:
        """
        Install plugin

        :param type: Plugin type
        :param file: Plugin ZIP archive
        :param repo_url: Git repository URL
        :return:
        """
        if settings.ENVIRONMENT != 'dev':
            raise errors.RequestError(msg='Plugins can only be installed in the development environment')
        if type == PluginType.zip:
            if not file:
                raise errors.RequestError(msg='ZIP archive must not be empty')
            return await install_zip_plugin(file)
        if not repo_url:
            raise errors.RequestError(msg='Git repository URL must not be empty')
        return await install_git_plugin(repo_url)

    @staticmethod
    async def uninstall(*, plugin: str) -> None:
        """
        Uninstall plugin

        :param plugin: Plugin name
        :return:
        """
        if settings.ENVIRONMENT != 'dev':
            raise errors.RequestError(msg='Plugins can only be uninstalled in the development environment')
        if plugin in get_required_plugins():
            raise errors.RequestError(msg=f'Plugin {plugin} is required and cannot be uninstalled')
        plugin_dir = anyio.Path(PLUGIN_DIR / plugin)
        if not await plugin_dir.exists():
            raise errors.NotFoundError(msg='Plugin does not exist')
        await uninstall_requirements_async(plugin)
        backup_file = PLUGIN_DIR / f'{plugin}.{timezone.now().strftime("%Y%m%d%H%M%S")}.backup.zip'
        await run_in_threadpool(zip_plugin, plugin_dir, backup_file)
        await run_in_threadpool(remove_plugin, plugin_dir)
        await redis_client.delete(f'{settings.PLUGIN_REDIS_PREFIX}:{plugin}')
        await redis_client.set(f'{settings.PLUGIN_REDIS_PREFIX}:changed', 'true')

    @staticmethod
    async def update_status(*, plugin: str) -> None:
        """
        Update plugin status

        :param plugin: Plugin name
        :return:
        """
        plugin_key = f'{settings.PLUGIN_REDIS_PREFIX}:{plugin}'
        plugin_info = await redis_client.get(plugin_key)
        if not plugin_info:
            raise errors.NotFoundError(msg='Plugin does not exist')
        plugin_info = json.loads(plugin_info)

        # Update persistent cache status
        new_status = (
            str(StatusType.enable.value)
            if plugin_info['plugin']['enable'] == str(StatusType.disable.value)
            else str(StatusType.disable.value)
        )
        plugin_info['plugin']['enable'] = new_status
        await redis_client.set(plugin_key, json.dumps(plugin_info, ensure_ascii=False))
        await redis_client.set(f'{settings.PLUGIN_REDIS_PREFIX}:changed', 'true')

    @staticmethod
    async def build(*, plugin: str) -> io.BytesIO:
        """
        Package plugin as a ZIP archive

        :param plugin: Plugin name
        :return:
        """
        plugin_dir = anyio.Path(PLUGIN_DIR / plugin)
        if not await plugin_dir.exists():
            raise errors.NotFoundError(msg='Plugin does not exist')

        bio = io.BytesIO()
        await run_in_threadpool(zip_plugin, plugin_dir, bio)
        bio.seek(0)
        return bio


plugin_service: PluginService = PluginService()
