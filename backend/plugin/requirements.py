import site
import subprocess
import sys

from importlib import invalidate_caches
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from starlette.concurrency import run_in_threadpool

from backend.core.conf import settings
from backend.core.path_conf import PLUGIN_DIR
from backend.plugin.core import get_plugins
from backend.plugin.errors import PluginInstallError


def _is_in_virtualenv() -> bool:
    """Check whether the process is running in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def _requirements_installed(requirements_file: Path) -> bool:  # ruff:ignore[complex-structure]
    """Check whether requirements and their extras dependencies are installed"""
    requirements = []
    for line in requirements_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            requirements.append(Requirement(line))
        except Exception as e:
            raise PluginInstallError(f'Invalid dependency {line}: {e!s}') from e

    environment = default_environment()
    visited = set()

    def requirement_satisfied(requirement: Requirement, active_extras: frozenset[str] = frozenset({''})) -> bool:
        if requirement.marker and not any(
            requirement.marker.evaluate(environment={**environment, 'extra': extra}) for extra in active_extras
        ):
            return True

        try:
            dist = distribution(requirement.name)
        except PackageNotFoundError:
            return False

        if requirement.specifier and not requirement.specifier.contains(dist.version, prereleases=True):
            return False

        requested_extras = tuple(sorted(requirement.extras))
        state = (canonicalize_name(requirement.name), requested_extras)
        if state in visited:
            return True
        visited.add(state)

        child_active_extras = frozenset(requirement.extras) or frozenset({''})
        for dependency_line in dist.requires or []:
            try:
                dependency = Requirement(dependency_line)
            except Exception as e:
                raise PluginInstallError(f'Invalid dependency metadata {dependency_line}: {e!s}') from e
            if not requirement_satisfied(dependency, child_active_extras):
                return False

        return True

    return all(requirement_satisfied(requirement) for requirement in requirements)


def install_requirements(plugin: str | None) -> None:  # ruff:ignore[complex-structure]
    """
    Install plugin dependencies

    :param plugin: Specify a plugin name; otherwise check all plugins
    :return:
    """
    plugins = [plugin] if plugin else get_plugins()

    for plugin in plugins:
        requirements_file = PLUGIN_DIR / plugin / 'requirements.txt'
        if not requirements_file.exists() or _requirements_installed(requirements_file):
            continue

        pip_install = ['uv', 'pip', 'install', '-r', str(requirements_file), '--prerelease=allow']
        if not _is_in_virtualenv():
            pip_install.append('--system')
        if settings.PLUGIN_PIP_CHINA:
            # Prioritize the China-based package index while retaining PyPI as a fallback
            pip_install.extend([
                '--index',
                settings.PLUGIN_PIP_INDEX_URL,
                '--index-strategy',
                'unsafe-best-match',
            ])

        max_retries = settings.PLUGIN_PIP_MAX_RETRY
        for attempt in range(max_retries):
            try:
                subprocess.check_call(pip_install)
                invalidate_caches()
                for site_dir in site.getsitepackages():
                    if site_dir.endswith('site-packages'):
                        site.addsitedir(site_dir)
                break
            except subprocess.TimeoutExpired:
                if attempt == max_retries - 1:
                    raise PluginInstallError(f'Dependency installation timed out for plugin {plugin}')
                continue
            except subprocess.CalledProcessError as e:
                if attempt == max_retries - 1:
                    raise PluginInstallError(f'Failed to install dependencies for plugin {plugin}: {e}') from e
                continue


def uninstall_requirements(plugin: str) -> None:
    """
    Uninstall plugin dependencies

    :param plugin: Plugin name
    :return:
    """
    requirements_file = PLUGIN_DIR / plugin / 'requirements.txt'
    if not requirements_file.exists():
        return

    try:
        pip_uninstall = ['uv', 'pip', 'uninstall', '-r', str(requirements_file)]
        if not _is_in_virtualenv():
            pip_uninstall.append('--system')
        subprocess.check_call(pip_uninstall, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise PluginInstallError(f'Failed to uninstall dependencies for plugin {plugin}: {e}') from e


async def install_requirements_async(plugin: str | None = None) -> None:
    """
    Install plugin dependencies asynchronously

    Windows platform limitations prevent a fully asynchronous implementation; details:
    https://stackoverflow.com/questions/44633458/why-am-i-getting-notimplementederror-with-async-and-await-on-windows
    """
    await run_in_threadpool(install_requirements, plugin)


async def uninstall_requirements_async(plugin: str) -> None:
    """
    Uninstall plugin dependencies asynchronously

    :param plugin: Plugin name
    :return:
    """
    await run_in_threadpool(uninstall_requirements, plugin)
