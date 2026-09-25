import io
import os
import re
import stat
import zipfile

import anyio

from anyio import open_file
from dulwich import porcelain
from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from backend.common.exception import errors
from backend.common.log import log
from backend.core.conf import settings
from backend.core.path_conf import ENV_FILE_PATH, PLUGIN_DIR
from backend.database.redis import redis_client
from backend.plugin.requirements import install_requirements_async
from backend.utils.locks import acquire_distributed_reload_lock
from backend.utils.pattern_validate import is_git_url


async def _append_env_example(plugin_path: anyio.Path) -> None:
    """
    Append to the main .env file

    :param plugin_path: Plugin directory path
    :return:
    """
    env_example_path = plugin_path / '.env.example'
    if not await env_example_path.exists():
        return

    async with await open_file(env_example_path, mode='r', encoding='utf-8') as f:
        env_example_content = await f.read()

    if not env_example_content.strip():
        return

    env_path = anyio.Path(ENV_FILE_PATH)
    existing_content = ''
    if await env_path.exists():
        async with await open_file(env_path, mode='r', encoding='utf-8') as f:
            existing_content = await f.read()

    separator = '\n' if existing_content and not existing_content.endswith('\n') else ''
    new_content = f'{existing_content}{separator}{env_example_content}'

    async with await open_file(env_path, mode='w', encoding='utf-8') as f:
        await f.write(new_content)


async def install_zip_plugin(file: UploadFile | str) -> str:  # ruff:ignore[complex-structure]
    """
    Install ZIP plugin

    :param file: FastAPI uploaded file object or full file path
    :return:
    """
    if isinstance(file, str):
        async with await open_file(file, mode='rb') as fb:
            contents = await fb.read()
    else:
        contents = await file.read()
    file_bytes = io.BytesIO(contents)
    if not zipfile.is_zipfile(file_bytes):
        raise errors.RequestError(msg='Invalid plugin archive format')

    async with acquire_distributed_reload_lock():
        with zipfile.ZipFile(file_bytes) as zf:
            # Validate archive
            plugin_namelist = zf.namelist()
            if not plugin_namelist:
                raise errors.RequestError(msg='Invalid plugin archive contents')
            plugin_dir_name = plugin_namelist[0].split('/', 1)[0].strip()
            if not plugin_dir_name:
                raise errors.RequestError(msg='Invalid plugin archive contents')
            if (
                len(plugin_namelist) <= 3
                or f'{plugin_dir_name}/plugin.toml' not in plugin_namelist
                or f'{plugin_dir_name}/README.md' not in plugin_namelist
            ):
                raise errors.RequestError(msg='Required files are missing from the plugin archive')

            # Whether the plugin can be installed
            plugin_name_match = re.match(
                r'^([a-zA-Z0-9_]+)',
                file.split(os.sep)[-1].split('.')[0].strip()
                if isinstance(file, str)
                else file.filename.split('.')[0].strip(),
            )
            if not plugin_name_match:
                raise errors.RequestError(msg='Invalid plugin archive filename')
            plugin_name = plugin_name_match.group()
            full_plugin_path = anyio.Path(PLUGIN_DIR / plugin_name)
            if await full_plugin_path.exists():
                raise errors.ConflictError(msg='This plugin is already installed')

            # Extract and install
            members = []
            prefix = f'{plugin_dir_name}/'
            for member in zf.infolist():
                if member.filename in {plugin_dir_name, prefix}:
                    continue
                if not member.filename.startswith(prefix):
                    continue

                relative_filename = member.filename.removeprefix(prefix)
                if not relative_filename:
                    if member.is_dir():
                        continue
                    raise errors.RequestError(msg='Invalid plugin archive contents')

                member.filename = relative_filename
                members.append(member)

            if not members:
                raise errors.RequestError(msg='Invalid plugin archive contents')

            await full_plugin_path.mkdir(parents=True, exist_ok=True)
            await run_in_threadpool(zf.extractall, full_plugin_path, members)

        await _append_env_example(full_plugin_path)
        await install_requirements_async(plugin_name)
        await redis_client.set(f'{settings.PLUGIN_REDIS_PREFIX}:changed', 'true')

    return plugin_name


async def install_git_plugin(repo_url: str) -> str:
    """
    Install Git plugin

    :param repo_url:
    :return:
    """
    match = is_git_url(repo_url)
    if not match:
        raise errors.RequestError(msg='Invalid Git repository URL; only HTTP/HTTPS is supported')
    repo_name = match.group('repo')
    path = anyio.Path(PLUGIN_DIR / repo_name)
    if await path.exists():
        raise errors.ConflictError(msg=f'Plugin {repo_name} is already installed')

    async with acquire_distributed_reload_lock():
        try:
            await run_in_threadpool(porcelain.clone, repo_url, PLUGIN_DIR / repo_name, checkout=True)
        except Exception as e:
            log.error(f'Plugin installation failed: {e}')
            raise errors.ServerError(msg='Plugin installation failed; please try again later') from e

        await _append_env_example(path)
        await install_requirements_async(repo_name)
        await redis_client.set(f'{settings.PLUGIN_REDIS_PREFIX}:changed', 'true')

    return repo_name


async def install_git_frontend_plugin(repo_url: str, frontend_project_root: str) -> str:
    """
    Install frontend Git plugin

    :param repo_url: Git repository URL
    :param frontend_project_root: Frontend project root path
    :return:
    """
    match = is_git_url(repo_url)
    if not match:
        raise errors.RequestError(msg='Invalid Git repository URL; only HTTP/HTTPS is supported')

    if not frontend_project_root.strip():
        raise errors.RequestError(msg='Frontend project root path must not be empty')

    frontend_root = await (await anyio.Path(frontend_project_root).expanduser()).resolve()
    if not await frontend_root.exists():
        raise errors.RequestError(msg='Frontend project root path does not exist')
    if not await frontend_root.is_dir():
        raise errors.RequestError(msg='Invalid frontend project root path')

    plugins_dir = frontend_root.joinpath('apps', 'web-antdv-next', 'src', 'plugins')
    if not await plugins_dir.exists() or not await plugins_dir.is_dir():
        raise errors.RequestError(
            msg=('Frontend plugin directory not found; ensure apps/web-antdv-next/src/plugins exists under this path')
        )

    repo_name = match.group('repo')
    # Repository names may end in _ui or -ui; omit that suffix from the installation directory
    plugin_name = repo_name.removesuffix('_ui') if repo_name.endswith('_ui') else repo_name.removesuffix('-ui')
    if not plugin_name:
        raise errors.RequestError(msg='Invalid frontend plugin repository name')

    target_path = anyio.Path(plugins_dir / plugin_name)
    if await target_path.exists():
        raise errors.ConflictError(msg=f'Frontend plugin {plugin_name} is already installed')

    try:
        await run_in_threadpool(porcelain.clone, repo_url, plugins_dir / plugin_name, checkout=True)
    except Exception as e:
        log.error(f'Frontend plugin installation failed: {e}')
        raise errors.ServerError(msg='Frontend plugin installation failed; please try again later') from e

    return plugin_name


def remove_plugin(plugin_dir: os.PathLike) -> None:
    """
    Delete plugin

    :param plugin_dir: Plugin directory
    :return:
    """
    import shutil

    def _on_error(func, path, _exc_info) -> None:  # ruff:ignore[missing-type-function-argument]
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(plugin_dir, onerror=_on_error)


def zip_plugin(plugin_dir: os.PathLike, target: os.PathLike | io.BytesIO) -> None:
    """
    Compress plugin as ZIP

    :param plugin_dir: Plugin directory
    :param target: Compression target
    :return:
    """
    with zipfile.ZipFile(target, 'w') as zf:
        plugin_dir_parent = os.path.dirname(plugin_dir)
        for root, dirs, files in os.walk(plugin_dir):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=plugin_dir_parent)
                zf.write(file_path, arcname)
