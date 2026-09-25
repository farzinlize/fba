import os
import warnings

from fastapi import APIRouter, Depends

from backend.common.dataclasses import PluginEntry
from backend.core.path_conf import PLUGIN_DIR
from backend.plugin.errors import PluginConfigError, PluginInjectError
from backend.plugin.status import PluginStatusChecker
from backend.utils.dynamic_import import import_module_cached


def _invalid_router_msg(plugin: str, module_path: str, level: str) -> str:
    return (
        f'{level} plugin {plugin} has no valid router in module {module_path}; check that the plugin files are complete'
    )


def inject_extend_router(plugin: PluginEntry) -> None:
    """
    Inject extension-level plugin routes

    :param plugin: Plugin name
    :return:
    """
    plugin_api_path = PLUGIN_DIR / plugin.name / 'api'
    if not os.path.exists(plugin_api_path):
        raise PluginConfigError(
            f'Plugin {plugin.name} is missing the api directory; check that the plugin files are complete'
        )

    for root, _, api_files in os.walk(plugin_api_path):
        for file in api_files:
            if not (file.endswith('.py') and file != '__init__.py'):
                continue

            # Parse plugin route configuration
            file_config = plugin.api[file[:-3]]
            prefix = file_config['prefix']
            tags = file_config['tags']

            # Get plugin route module
            file_path = os.path.join(root, file)
            path_to_module_str = os.path.relpath(file_path, PLUGIN_DIR).replace(os.sep, '.')[:-3]
            module_path = f'backend.plugin.{path_to_module_str}'

            try:
                module = import_module_cached(module_path)
                plugin_router = getattr(module, 'router', None)
                if not plugin_router:
                    msg = _invalid_router_msg(plugin.name, module_path, 'Extension level')
                    warnings.warn(
                        msg,
                        FutureWarning,
                    )
                    continue

                # Get target application routes
                relative_path = os.path.relpath(root, plugin_api_path)
                app_name = plugin.extend
                target_module_path = f'backend.app.{app_name}.api.{relative_path.replace(os.sep, ".")}'
                target_module = import_module_cached(target_module_path)
                target_router = getattr(target_module, 'router', None)

                if not target_router or not isinstance(target_router, APIRouter):
                    raise PluginInjectError(_invalid_router_msg(plugin.name, module_path, 'Extension level'))

                # Inject plugin routes into the target router
                target_router.include_router(
                    router=plugin_router,
                    prefix=prefix,
                    tags=[tags] if tags else [],
                    dependencies=[Depends(PluginStatusChecker(plugin.name))],
                )
            except Exception as e:
                raise PluginInjectError(
                    f'Route injection failed for extension-level plugin {plugin.name}: {e!s}'
                ) from e


def inject_app_router(plugin: PluginEntry, target_router: APIRouter) -> None:
    """
    Inject application-level plugin routes

    :param plugin: Plugin name
    :param target_router: FastAPI router
    :return:
    """
    module_path = f'backend.plugin.{plugin.name}.api.router'
    try:
        module = import_module_cached(module_path)
        routers = plugin.routers
        if not routers or not isinstance(routers, list):
            raise PluginConfigError(
                f'Application-level plugin {plugin.name} has an invalid configuration file; please check it'
            )

        for router in routers:
            plugin_router = getattr(module, router, None)
            if not plugin_router or not isinstance(plugin_router, APIRouter):
                raise PluginInjectError(_invalid_router_msg(plugin.name, module_path, 'Application level'))

            # Inject plugin routes into the target router
            target_router.include_router(plugin_router, dependencies=[Depends(PluginStatusChecker(plugin.name))])
    except Exception as e:
        raise PluginInjectError(f'Route injection failed for application-level plugin {plugin.name}: {e!s}') from e


def build_final_router() -> APIRouter:
    """Build final routes"""
    from backend.plugin.core import parse_plugin_config, resolve_plugin_order

    extend_plugins, app_plugins = parse_plugin_config()
    plugins = extend_plugins + app_plugins
    ordered_plugins = resolve_plugin_order(plugins)

    for plugin in ordered_plugins:
        if plugin.api is not None:
            inject_extend_router(plugin)

    # Import the main router after extension-level route injection and before application-level route injection
    from backend.app.router import router as main_router

    for plugin in ordered_plugins:
        if plugin.routers is not None:
            inject_app_router(plugin, main_router)

    return main_router
