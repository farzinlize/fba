import json
import os

from functools import lru_cache
from typing import Any

import rtoml

from backend.common.dataclasses import PluginEntry
from backend.common.enums import PluginLevelType, StatusType
from backend.common.log import log
from backend.core.conf import settings
from backend.core.path_conf import PLUGIN_DIR
from backend.database.redis import RedisCli
from backend.plugin.errors import PluginConfigError, PluginInjectError
from backend.plugin.status import get_plugin_enable
from backend.plugin.validator import validate_plugin_config
from backend.utils.async_helper import run_await
from backend.utils.dynamic_import import get_model_objects


def check_plugin_installed(plugin_name: str) -> bool:
    """
    Check whether plugin is installed

    :param plugin_name: Plugin name
    :return:
    """
    return (PLUGIN_DIR / plugin_name / '__init__.py').exists()


def get_required_plugins() -> tuple[str, ...]:
    """Get required plugin list"""
    required_plugins = list(settings.PLUGIN_REQUIRED)
    if not settings.RBAC_ROLE_MENU_MODE and 'casbin_rbac' not in required_plugins:
        required_plugins.append('casbin_rbac')
    return tuple(required_plugins)


def check_required_plugins() -> None:
    """Check required plugins"""
    required_plugins = get_required_plugins()
    missing_plugins = [name for name in required_plugins if not check_plugin_installed(name)]
    if missing_plugins:
        raise PluginInjectError(f'Required plugins are missing: {", ".join(missing_plugins)}; install them first')


@lru_cache(maxsize=128)
def get_plugins() -> tuple[str, ...]:
    """Get plugin list"""
    plugin_packages = []

    # Iterate over plugin directories
    for item in os.listdir(PLUGIN_DIR):
        item_path = PLUGIN_DIR / item
        if not os.path.isdir(item_path) and item == '__pycache__':
            continue

        # Check that the entry is a directory containing __init__.py
        if os.path.isdir(item_path) and '__init__.py' in os.listdir(item_path):
            plugin_packages.append(item)

    return tuple(plugin_packages)


def get_enabled_plugins(plugins: tuple[str, ...] | None = None) -> set[str]:
    """
    Get enabled plugin list

    :param plugins: Plugin name list
    :return:
    """
    plugin_names = plugins or get_plugins()
    enabled_plugins = set(plugin_names)

    current_redis_client = RedisCli()
    run_await(current_redis_client.init)()

    try:
        for plugin in plugin_names:
            plugin_info = run_await(current_redis_client.get)(f'{settings.PLUGIN_REDIS_PREFIX}:{plugin}')
            if get_plugin_enable(plugin_info, StatusType.enable.value) != str(StatusType.enable.value):
                enabled_plugins.discard(plugin)
    finally:
        run_await(current_redis_client.aclose)()

    return enabled_plugins


def load_plugin_config(plugin: str) -> dict[str, Any]:
    """
    Load plugin configuration

    :param plugin: Plugin name
    :return:
    """
    toml_path = PLUGIN_DIR / plugin / 'plugin.toml'
    if not os.path.exists(toml_path):
        raise PluginInjectError(f'Plugin {plugin} is missing plugin.toml; check that the plugin is valid')

    with open(toml_path, encoding='utf-8') as f:
        return rtoml.load(f)


def parse_plugin_config() -> tuple[list[PluginEntry], list[PluginEntry]]:
    """Parse plugin configuration"""
    plugins = get_plugins()
    extend_plugins: list[PluginEntry] = []
    app_plugins: list[PluginEntry] = []

    # Use a dedicated connection
    current_redis_client = RedisCli()
    run_await(current_redis_client.init)()

    try:
        # Remove information for unknown plugins
        exclude_keys = [f'{settings.PLUGIN_REDIS_PREFIX}:{key}' for key in plugins]
        run_await(current_redis_client.delete_by_prefix)(
            settings.PLUGIN_REDIS_PREFIX,
            exclude_keys=exclude_keys,
        )

        for plugin in plugins:
            plugin_config = load_plugin_config(plugin)
            plugin_type = validate_plugin_config(plugin, plugin_config)

            # Populate plugin information
            plugin_config['plugin']['name'] = plugin
            plugin_cache_key = f'{settings.PLUGIN_REDIS_PREFIX}:{plugin}'
            plugin_cache_info = run_await(current_redis_client.get)(plugin_cache_key)
            plugin_config['plugin']['enable'] = get_plugin_enable(plugin_cache_info, StatusType.enable.value)

            if plugin_type == PluginLevelType.extend:
                extend_plugins.append(
                    PluginEntry(
                        name=plugin,
                        depends_on=plugin_config['plugin'].get('depends_on'),
                        extend=plugin_config['app']['extend'],
                        api=plugin_config['api'],
                    )
                )
            elif plugin_type == PluginLevelType.app:
                app_plugins.append(
                    PluginEntry(
                        name=plugin,
                        depends_on=plugin_config['plugin'].get('depends_on'),
                        routers=plugin_config['app']['router'],
                    )
                )

            # Cache latest plugin information
            run_await(current_redis_client.set)(plugin_cache_key, json.dumps(plugin_config, ensure_ascii=False))

        # Reset plugin change status
        run_await(current_redis_client.delete)(f'{settings.PLUGIN_REDIS_PREFIX}:changed')
    finally:
        run_await(current_redis_client.aclose)()

    return extend_plugins, app_plugins


def resolve_plugin_order(plugins: list[PluginEntry]) -> list[PluginEntry]:
    """
    Sort plugins by depends_on

    :param plugins: Plugin configuration list
    :return:
    """
    plugin_map = {plugin.name: plugin for plugin in plugins}
    ordered_plugins: list[PluginEntry] = []
    visited: set[str] = set()
    visiting: list[str] = []

    def visit(plugin: PluginEntry) -> None:
        if plugin.name in visited:
            return
        if plugin.name in visiting:
            cycle_start = visiting.index(plugin.name)
            cycle_path = [*visiting[cycle_start:], plugin.name]
            raise PluginConfigError(f'Circular plugin dependency: {" -> ".join(cycle_path)}')

        if plugin.depends_on is not None:
            visiting.append(plugin.name)
            for dep_name in plugin.depends_on:
                dep_plugin = plugin_map.get(dep_name)
                if dep_plugin is None:
                    raise PluginConfigError(
                        f'Plugin {plugin.name} depends on plugin {dep_name}, but plugin {dep_name} does not exist'
                    )
                visit(dep_plugin)
            visiting.pop()

        visited.add(plugin.name)
        ordered_plugins.append(plugin)

    for plugin in plugins:
        visit(plugin)

    return ordered_plugins


def get_ordered_enabled_plugins() -> list[PluginEntry]:
    """Get enabled plugins in dependency order"""
    enabled_plugins = get_enabled_plugins()
    extend_plugins, app_plugins = parse_plugin_config()
    plugins: list[PluginEntry] = [plugin for plugin in extend_plugins + app_plugins if plugin.name in enabled_plugins]

    try:
        return resolve_plugin_order(plugins)
    except PluginConfigError as e:
        log.error(f'Failed to resolve plugin dependencies: {e}')
        raise


def get_plugin_models() -> list[object]:
    """Get all model classes from plugins"""
    objs = []

    for plugin in get_plugins():
        module_path = f'backend.plugin.{plugin}.model'
        model_objs = get_model_objects(module_path)
        if model_objs:
            objs.extend(model_objs)

    return objs
