import asyncio
import re
import secrets
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Final, Literal

import anyio
import cappa
import granian

from cappa.output import error_format
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.text import Text
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from starlette.concurrency import run_in_threadpool
from watchfiles import Change, PythonFilter

from backend import __version__
from backend.common.dataclasses import PluginEntry
from backend.common.enums import DataBaseType, PrimaryKeyType
from backend.common.exception.errors import BaseExceptionError
from backend.common.model import MappedBase
from backend.core.conf import settings
from backend.core.path_conf import (
    BASE_PATH,
    ENV_EXAMPLE_FILE_PATH,
    ENV_FILE_PATH,
    LOCALE_DIR,
    MYSQL_SCRIPT_DIR,
    PLUGIN_DIR,
    POSTGRESQL_SCRIPT_DIR,
    RELOAD_LOCK_FILE,
)
from backend.database.db import (
    async_db_session,
    create_database_async_engine,
    create_database_async_session,
    get_database_url,
)
from backend.database.redis import RedisCli, redis_client
from backend.plugin.core import (
    get_plugins,
    get_required_plugins,
    load_plugin_config,
    resolve_plugin_order,
)
from backend.plugin.installer import install_git_frontend_plugin, install_git_plugin, install_zip_plugin, zip_plugin
from backend.plugin.installer import remove_plugin as _remove_plugin
from backend.plugin.requirements import install_requirements_async, uninstall_requirements_async
from backend.plugin.sql import build_sql_filename, get_plugin_destroy_sql, get_plugin_sql
from backend.plugin.validator import validate_plugin_config
from backend.utils.console import console
from backend.utils.dynamic_import import import_module_cached
from backend.utils.sql_parser import parse_sql_script
from backend.utils.timezone import timezone

_OUTPUT_HELP: Final = "\nFor more information, try '[cyan]--help[/]'"


class CustomReloadFilter(PythonFilter):
    """Custom reload filter"""

    def __init__(self) -> None:
        self.extra_extensions = ('.json', '.yaml', '.yml')
        super().__init__(extra_extensions=self.extra_extensions)

    def __call__(self, change: Change, path: str) -> bool:
        if RELOAD_LOCK_FILE.exists():
            return False

        file_path = Path(path).resolve()
        if file_path.suffix in self.extra_extensions and not file_path.is_relative_to(LOCALE_DIR.resolve()):
            return False

        return super().__call__(change, path)


def setup_env_file() -> bool:
    """Interactively configure and generate the .env environment file"""
    if not ENV_EXAMPLE_FILE_PATH.exists():
        console.caution('.env.example file does not exist')
        return False

    try:
        env_content = Path(ENV_EXAMPLE_FILE_PATH).read_text(encoding='utf-8')
        console.note('Configure database connection...')
        db_type = Prompt.ask('Database type', choices=['mysql', 'postgresql'], default='postgresql')
        db_host = Prompt.ask('Database host', default='127.0.0.1')
        db_port = Prompt.ask('Database port', default='5432' if db_type == 'postgresql' else '3306')
        db_user = Prompt.ask('Database username', default='postgres' if db_type == 'postgresql' else 'root')
        db_password = Prompt.ask('Database password', password=True, default='123456')

        console.note('Configure Redis connection...')
        redis_host = Prompt.ask('Redis host', default='127.0.0.1')
        redis_port = Prompt.ask('Redis port', default='6379')
        redis_password = Prompt.ask('Redis password (leave blank for no password)', password=True, default='')
        redis_db = Prompt.ask('Redis database number', default='0')

        console.info('Generate token secret...')
        token_secret = secrets.token_urlsafe(32)

        console.info('Write .env file...')
        env_content = env_content.replace("DATABASE_TYPE='postgresql'", f"DATABASE_TYPE='{db_type}'")
        settings.DATABASE_TYPE = db_type
        env_content = env_content.replace("DATABASE_HOST='127.0.0.1'", f"DATABASE_HOST='{db_host}'")
        settings.DATABASE_HOST = db_host
        env_content = env_content.replace('DATABASE_PORT=5432', f'DATABASE_PORT={db_port}')
        settings.DATABASE_PORT = db_port
        env_content = env_content.replace("DATABASE_USER='postgres'", f"DATABASE_USER='{db_user}'")
        settings.DATABASE_USER = db_user
        env_content = env_content.replace("DATABASE_PASSWORD='123456'", f"DATABASE_PASSWORD='{db_password}'")
        settings.DATABASE_PASSWORD = db_password
        env_content = env_content.replace("REDIS_HOST='127.0.0.1'", f"REDIS_HOST='{redis_host}'")
        settings.REDIS_HOST = redis_host
        env_content = env_content.replace('REDIS_PORT=6379', f'REDIS_PORT={redis_port}')
        settings.REDIS_PORT = redis_port
        env_content = env_content.replace("REDIS_PASSWORD=''", f"REDIS_PASSWORD='{redis_password}'")
        settings.REDIS_PASSWORD = redis_password
        env_content = env_content.replace('REDIS_DATABASE=0', f'REDIS_DATABASE={redis_db}')
        settings.REDIS_DATABASE = redis_db
        env_content = re.sub(r"TOKEN_SECRET_KEY='[^']*'", f"TOKEN_SECRET_KEY='{token_secret}'", env_content)
        settings.TOKEN_SECRET_KEY = token_secret

        Path(ENV_FILE_PATH).write_text(env_content, encoding='utf-8')
        console.tip('.env file created successfully')
    except Exception as e:
        console.caution(f'Failed to create .env file: {e}')
        return False
    else:
        return True


async def create_database(conn: AsyncConnection) -> bool:
    """Create or recreate database"""
    try:
        terminate_sql = None
        if DataBaseType.mysql == settings.DATABASE_TYPE:
            check_sql = f"SHOW DATABASES LIKE '{settings.DATABASE_SCHEMA}'"
            drop_sql = f'DROP DATABASE IF EXISTS `{settings.DATABASE_SCHEMA}`'
            create_sql = (
                f'CREATE DATABASE `{settings.DATABASE_SCHEMA}` CHARACTER SET {settings.DATABASE_CHARSET} '
                f'COLLATE {settings.DATABASE_CHARSET}_unicode_ci'
            )
        else:
            check_sql = f"SELECT 1 FROM pg_database WHERE datname = '{settings.DATABASE_SCHEMA}'"
            drop_sql = f'DROP DATABASE IF EXISTS {settings.DATABASE_SCHEMA}'
            create_sql = f'CREATE DATABASE {settings.DATABASE_SCHEMA}'
            terminate_sql = (
                f'SELECT pg_terminate_backend(pid) FROM pg_stat_activity '
                f"WHERE datname = '{settings.DATABASE_SCHEMA}' AND pid <> pg_backend_pid()"
            )

        result = await conn.execute(text(check_sql))
        exists = result.fetchone() is not None
        console.note(f'Recreating database {settings.DATABASE_SCHEMA}...')
        if exists:
            if terminate_sql:
                await conn.execute(text(terminate_sql))
            await conn.execute(text(drop_sql))
        await conn.execute(text(create_sql))
        console.tip('Database created successfully')
    except Exception as e:
        console.caution(f'Failed to create database: {e}')
        return False
    else:
        return True


def _build_db_config_panel_content() -> Text:
    """Build database configuration panel content"""
    panel_content = Text()
    panel_content.append('[Database configuration]', style='bold green')
    panel_content.append('\n\n  • Type: ')
    panel_content.append(f'{settings.DATABASE_TYPE}', style='yellow')
    panel_content.append('\n  • Host: ')
    panel_content.append(f'{settings.DATABASE_HOST}:{settings.DATABASE_PORT}', style='yellow')
    panel_content.append('\n  • Database: ')
    panel_content.append(f'{settings.DATABASE_SCHEMA}', style='yellow')
    panel_content.append('\n  • Primary key mode: ')
    panel_content.append(f'{settings.DATABASE_PK_MODE}', style='yellow')
    return panel_content


async def auto_init() -> None:
    """Automated initialization workflow"""
    console.print('\n[bold cyan]Step 1/3:[/] Configure environment variables', style='bold')
    panel_content = Text()
    panel_content.append('[Environment configuration]', style='bold green')
    panel_content.append('\n\n  • Database connection')
    panel_content.append('\n  • Redis connection')
    panel_content.append('\n  • Token secret (automatically generated)')

    console.print(
        Panel(panel_content, title=f'fba (v{__version__}) - Environment variables', border_style='cyan', padding=(1, 2))
    )
    if not setup_env_file():
        raise cappa.Exit('Failed to configure .env file', code=1)

    console.print('\n[bold cyan]Step 2/3:[/] Create database', style='bold')
    panel_content = _build_db_config_panel_content()

    console.print(Panel(panel_content, title=f'fba (v{__version__}) - Database', border_style='cyan', padding=(1, 2)))
    ok = Prompt.ask('About to [red]create/recreate the database[/red]. Continue?', choices=['y', 'n'], default='n')

    if ok.lower() == 'y':
        async_init_engine = create_database_async_engine(get_database_url(with_database=False))
        async with async_init_engine.connect() as conn:
            await conn.execution_options(isolation_level='AUTOCOMMIT')
            if not await create_database(conn):
                raise cappa.Exit('Failed to create database', code=1)
    else:
        console.warning('Database operation canceled')

    console.print('\n[bold cyan]Step 3/3:[/] Initialize database tables and data', style='bold')
    async_init_engine = create_database_async_engine(get_database_url())
    async_init_db_session = create_database_async_session(async_init_engine)
    redis_init_client = RedisCli(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DATABASE,
    )
    await redis_init_client.init()
    async with async_init_db_session.begin() as db:
        await init(db, redis_init_client)


async def init(db: AsyncSession, redis: RedisCli) -> None:
    """Interactively initialize database schema and data"""
    panel_content = _build_db_config_panel_content()
    pk_details = panel_content.from_markup(
        '[link=https://docs.fba.wu-clan.cc/fastapi_best_architecture_docs/backend/reference/pk.html](Learn more)[/]'
    )
    panel_content.append(pk_details)
    panel_content.append('\n\n[Redis configuration]', style='bold green')
    panel_content.append('\n\n  • Host: ')
    panel_content.append(f'{settings.REDIS_HOST}:{settings.REDIS_PORT}', style='yellow')
    panel_content.append('\n  • Database: ')
    panel_content.append(f'{settings.REDIS_DATABASE}', style='yellow')
    plugins = get_plugins()
    panel_content.append('\n\n[Installed plugins]', style='bold green')
    panel_content.append('\n\n  • ')
    if plugins:
        panel_content.append(f'{", ".join(plugins)}', style='yellow')
    else:
        panel_content.append('None', style='dim')

    console.print(
        Panel(panel_content, title=f'fba (v{__version__}) - Initialization', border_style='cyan', padding=(1, 2))
    )
    ok = Prompt.ask(
        ('About to [red]create/recreate database tables[/red] and [red]execute all database scripts[/red]. Continue?'),
        choices=['y', 'n'],
        default='n',
    )

    if ok.lower() == 'y':
        try:
            console.note('Clear Redis cache')
            for prefix in [
                settings.JWT_USER_REDIS_PREFIX,
                settings.TOKEN_EXTRA_INFO_REDIS_PREFIX,
                settings.TOKEN_ONLINE_REDIS_PREFIX,
                settings.TOKEN_REDIS_PREFIX,
                settings.TOKEN_REFRESH_REDIS_PREFIX,
                settings.TOKEN_SESSION_REDIS_PREFIX,
            ]:
                await redis.delete_by_prefix(prefix)

            console.note('Recreate database tables')
            conn = await db.connection()
            await conn.run_sync(MappedBase.metadata.drop_all)
            await conn.run_sync(MappedBase.metadata.create_all)

            console.note('Execute SQL scripts')
            sql_scripts = await get_sql_scripts()
            for sql_script in sql_scripts:
                console.note(f'Executing: {sql_script}')
                await execute_sql_scripts(db, sql_script, is_init=True)

            console.tip('Initialization successful')
            console.print('\nTry [bold cyan]fba run[/bold cyan] to start the service!')
        except Exception as e:
            raise cappa.Exit(f'Initialization failed: {e}', code=1)
    else:
        console.warning('Initialization canceled')


def run(host: str, port: int, reload: bool, workers: int) -> None:  # ruff:ignore[boolean-type-hint-positional-argument]
    """Start API service"""
    url = f'http://{host}:{port}'
    docs_url = url + settings.FASTAPI_DOCS_URL
    redoc_url = url + settings.FASTAPI_REDOC_URL
    openapi_url = url + (settings.FASTAPI_OPENAPI_URL or '')

    panel_content = Text()
    panel_content.append('Python version: ', style='bold cyan')
    panel_content.append(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}', style='white')

    panel_content.append('\nAPI URL: ', style='bold cyan')
    panel_content.append(f'{url}{settings.FASTAPI_API_V1_PATH}', style='blue')

    panel_content.append('\n\nEnvironment: ', style='bold green')
    env_style = 'yellow' if settings.ENVIRONMENT == 'dev' else 'green'
    panel_content.append(f'{settings.ENVIRONMENT.upper()}', style=env_style)

    plugins = get_plugins()
    panel_content.append('\nInstalled plugins: ', style='bold green')
    if plugins:
        panel_content.append(f'{", ".join(plugins)}', style='yellow')
    else:
        panel_content.append('None', style='white')

    if settings.ENVIRONMENT == 'dev':
        panel_content.append(f'\n\n📖 Swagger documentation: {docs_url}', style='bold magenta')
        panel_content.append(f'\n📚 ReDoc documentation: {redoc_url}', style='bold magenta')
        panel_content.append(f'\n📡 OpenAPI JSON: {openapi_url}', style='bold magenta')

    panel_content.append('\n🌐 Official architecture documentation: ', style='bold magenta')
    panel_content.append('https://docs.fba.wu-clan.cc/fastapi_best_architecture_docs/')

    panel_content.append('\n\nSponsors: ', style='bold yellow')
    panel_content.append('Claude.uy', style='link https://claude.uy/home')

    console.print(Panel(panel_content, title=f'fba (v{__version__})', border_style='purple', padding=(1, 2)))
    granian.Granian(
        target='backend.main:app',
        interface='asgi',
        address=host,
        port=port,
        reload=not reload,
        reload_filter=CustomReloadFilter,
        workers=workers,
    ).serve()


def run_celery_worker(log_level: Literal['info', 'debug']) -> None:
    """Start Celery worker service"""
    try:
        subprocess.run(['celery', '-A', 'backend.app.task.celery', 'worker', '-l', f'{log_level}', '-P', 'gevent'])
    except KeyboardInterrupt:
        pass


def run_celery_beat(log_level: Literal['info', 'debug']) -> None:
    """Start Celery beat scheduler service"""
    try:
        subprocess.run(['celery', '-A', 'backend.app.task.celery', 'beat', '-l', f'{log_level}'])
    except KeyboardInterrupt:
        pass


def run_celery_flower(port: int, basic_auth: str) -> None:
    """Start Celery Flower monitoring service"""
    try:
        subprocess.run([
            'celery',
            '-A',
            'backend.app.task.celery',
            'flower',
            f'--port={port}',
            f'--basic-auth={basic_auth}',
        ])
    except KeyboardInterrupt:
        pass


async def install_plugin(  # ruff:ignore[complex-structure]
    path: str | None,
    repo_url: str | None,
    frontend: bool,  # ruff:ignore[boolean-type-hint-positional-argument]
    no_sql: bool,  # ruff:ignore[boolean-type-hint-positional-argument]
    db_type: DataBaseType,
    pk_type: PrimaryKeyType,
) -> None:
    """Install plugin"""
    if settings.ENVIRONMENT != 'dev':
        raise cappa.Exit('Plugins can only be installed in the development environment', code=1)

    plugin_name = None
    console.note('Installing plugin...')

    try:
        if frontend:
            if repo_url is None:
                raise cappa.Exit('Frontend plugins can only be installed from a Git repository URL', code=1)

            frontend_project_root = Prompt.ask('Enter the frontend project root path')
            plugin_name = await install_git_frontend_plugin(repo_url, frontend_project_root)
            console.tip(f'Frontend plugin {plugin_name} installed successfully')
            return

        if path is None and repo_url is None:
            raise cappa.Exit('Specify either path or repo_url', code=1)
        if path and repo_url:
            raise cappa.Exit('path and repo_url cannot both be specified', code=1)

        if path:
            plugin_name = await install_zip_plugin(file=path)
        if repo_url:
            plugin_name = await install_git_plugin(repo_url=repo_url)

        console.tip(f'Plugin {plugin_name} installed successfully')

        console.note(f'Synchronizing database tables for plugin {plugin_name}...')
        try:
            import_module_cached(f'backend.plugin.{plugin_name}.model')
        except ModuleNotFoundError:
            pass
        else:
            async with async_db_session.begin() as db:
                conn = await db.connection()
                await conn.run_sync(MappedBase.metadata.create_all)

        if not no_sql:
            sql_file = await get_plugin_sql(plugin_name, db_type, pk_type)
            if sql_file:
                console.info(f'Executing initialization SQL script for plugin {plugin_name}: {sql_file}')
                async with async_db_session.begin() as db:
                    await execute_sql_scripts(db, sql_file)
            else:
                console.warning(
                    f'Plugin {plugin_name} provides no initialization SQL script; skipping database initialization'
                )

    except Exception as e:
        raise cappa.Exit(e.msg if isinstance(e, BaseExceptionError) else str(e), code=1)


def should_sync_plugin_deps(plugin: str | None, *, allow_empty: bool) -> bool:
    """Check whether plugin dependencies need synchronization"""
    plugins = get_plugins()
    if plugin is not None and plugin not in plugins:
        raise cappa.Exit(f'Plugin {plugin} does not exist', code=1)
    if not plugins:
        if allow_empty:
            console.warning('No plugins installed; skipping plugin dependency synchronization')
            return False
        raise cappa.Exit('No plugins are currently installed', code=1)
    return True


async def sync_project_deps() -> None:
    """Synchronize project dependencies"""
    console.note('Synchronizing project dependencies...')
    try:
        await run_in_threadpool(subprocess.run, ['uv', 'sync'], cwd=BASE_PATH.parent, check=True)
    except FileNotFoundError:
        raise cappa.Exit('uv is not installed; install uv first', code=1)
    except subprocess.CalledProcessError as e:
        raise cappa.Exit('Failed to synchronize project dependencies', code=e.returncode)
    console.tip('Project dependencies synchronized')


async def sync_plugin_deps(plugin: str | None = None) -> None:
    """Synchronize plugin dependencies"""
    console.note(
        f'Installing dependencies for plugin {plugin}...' if plugin else 'Installing dependencies for all plugins...'
    )
    try:
        await install_requirements_async(plugin)
    except Exception as e:
        raise cappa.Exit(e.msg if isinstance(e, BaseExceptionError) else str(e), code=1)
    console.tip(f'Dependencies for plugin {plugin} installed' if plugin else 'All plugin dependencies installed')


async def sync_deps(plugin: str | None, *, no_project: bool = False, no_plugin: bool = False) -> None:
    """Synchronize project and plugin dependencies"""
    if no_project and no_plugin:
        raise cappa.Exit('--no-project and --no-plugin cannot be used together', code=1)
    if plugin is not None and no_plugin:
        raise cappa.Exit('--plugin and --no-plugin cannot be used together', code=1)

    should_sync_plugins = False if no_plugin else should_sync_plugin_deps(plugin, allow_empty=not no_project)
    if not no_project:
        await sync_project_deps()
    if should_sync_plugins:
        await sync_plugin_deps(plugin)


async def remove_plugin(plugin: str | None, *, no_sql: bool = False) -> None:  # ruff:ignore[complex-structure]
    """Uninstall plugin"""
    if settings.ENVIRONMENT != 'dev':
        raise cappa.Exit('Plugins can only be uninstalled in the development environment', code=1)

    async def remove() -> None:
        plugin_dir = PLUGIN_DIR / plugin
        if not plugin_dir.exists():
            raise cappa.Exit(f'Plugin {plugin} does not exist', code=1)

        if not no_sql:
            destroy_sql_file = await get_plugin_destroy_sql(plugin, settings.DATABASE_TYPE, settings.DATABASE_PK_MODE)
            if destroy_sql_file:
                console.note(f'Executing teardown SQL script for plugin {plugin}: {destroy_sql_file}')
                async with async_db_session.begin() as db:
                    await execute_destroy_sql_scripts(db, destroy_sql_file)
            else:
                console.warning(f'Plugin {plugin} provides no teardown SQL script; skipping database cleanup')

        console.note(f'Uninstalling dependencies for plugin {plugin}...')
        await uninstall_requirements_async(plugin)

        console.note(f'Backing up plugin {plugin}...')
        backup_file = PLUGIN_DIR / f'{plugin}.{timezone.now().strftime("%Y%m%d%H%M%S")}.backup.zip'
        await run_in_threadpool(zip_plugin, plugin_dir, backup_file)
        await run_in_threadpool(_remove_plugin, plugin_dir)

        console.note(f'Backup file: {backup_file}')
        console.tip(f'Plugin {plugin} uninstalled successfully')
        console.print()
        console.warning('Remove related configuration according to the plugin README.md and restart the service')

    plugins = get_plugins()
    if not plugins:
        raise cappa.Exit('No plugins are currently installed', code=1)

    if not plugin:
        table = Table(show_header=True, header_style='bold magenta')
        table.add_column('Number', style='cyan', no_wrap=True, justify='center')
        table.add_column('Plugin name', style='green', no_wrap=True)

        for idx, name in enumerate(plugins, 1):
            table.add_row(str(idx), name)

        console.print(table)
        choice = IntPrompt.ask(
            'Select the number of the plugin to uninstall', choices=[str(i) for i in range(1, len(plugins) + 1)]
        )
        plugin = plugins[choice - 1]
    else:
        if plugin not in plugins:
            raise cappa.Exit(f'Plugin {plugin} does not exist', code=1)

    if plugin in get_required_plugins():
        raise cappa.Exit(f'Plugin {plugin} is required and cannot be uninstalled', code=1)

    try:
        await remove()
    except Exception as e:
        raise cappa.Exit(f'Plugin uninstallation failed: {e}', code=1)


async def get_sql_scripts() -> list[str]:
    """Get paths of all pending SQL scripts"""
    sql_scripts: list[str] = []
    db_script_dir = MYSQL_SCRIPT_DIR if DataBaseType.mysql == settings.DATABASE_TYPE else POSTGRESQL_SCRIPT_DIR
    main_sql_file = db_script_dir / build_sql_filename(
        'init',
        settings.DATABASE_PK_MODE,
        suffix='test_data',
    )

    if await anyio.Path(main_sql_file).exists():
        sql_scripts.append(str(main_sql_file))

    plugins = []
    for plugin in get_plugins():
        plugin_config = load_plugin_config(plugin)
        validate_plugin_config(plugin, plugin_config)
        plugins.append(PluginEntry(name=plugin, depends_on=plugin_config['plugin'].get('depends_on')))

    for plugin in resolve_plugin_order(plugins):
        plugin_sql = await get_plugin_sql(plugin.name, settings.DATABASE_TYPE, settings.DATABASE_PK_MODE)
        if plugin_sql:
            sql_scripts.append(plugin_sql)

    return sql_scripts


async def execute_sql_scripts(db: AsyncSession, sql_scripts: str, *, is_init: bool = False) -> None:
    """Parse and execute SQL scripts"""
    try:
        stmts = await parse_sql_script(sql_scripts)
        conn = await db.connection()
        for stmt in stmts:
            await conn.exec_driver_sql(stmt)
    except Exception as e:
        raise cappa.Exit(f'SQL script execution failed: {e}', code=1)

    if not is_init:
        console.tip('SQL scripts executed successfully')


async def execute_destroy_sql_scripts(db: AsyncSession, sql_scripts: str) -> None:
    """Execute plugin teardown SQL scripts"""
    try:
        stmts = await parse_sql_script(sql_scripts, is_destroy=True)
        conn = await db.connection()
        for stmt in stmts:
            await conn.exec_driver_sql(stmt)
    except Exception as e:
        raise cappa.Exit(f'Teardown SQL script execution failed: {e}', code=1)

    console.tip('Teardown SQL scripts executed successfully')


async def import_table(
    app: str,
    table_schema: str,
    table_name: str,
) -> None:
    """Import code generation business definitions and model columns"""
    if settings.ENVIRONMENT != 'dev':
        raise cappa.Exit('Code generation is only available in the development environment', code=1)

    try:
        from backend.plugin.code_generator.schema.code_gen import ImportParam
        from backend.plugin.code_generator.service.code_gen_service import code_gen_service
    except ImportError:
        raise cappa.Exit('Failed to import code generator plugin utilities; contact the system administrator', code=1)

    try:
        obj = ImportParam(app=app, table_schema=table_schema, table_name=table_name)
        async with async_db_session.begin() as db:
            await code_gen_service.import_business_and_model(db=db, obj=obj)
        console.tip('Code generation business definitions and model columns imported successfully')
        console.log('\nTry [bold cyan]fba codegen[/bold cyan] to generate code!')
    except Exception as e:
        raise cappa.Exit(e.msg if isinstance(e, BaseExceptionError) else str(e), code=1)


async def generate(*, preview: bool = False) -> None:
    """Interactive code generation"""
    if settings.ENVIRONMENT != 'dev':
        raise cappa.Exit('Code generation is only available in the development environment', code=1)

    try:
        from backend.plugin.code_generator.service.business_service import code_gen_business_service
        from backend.plugin.code_generator.service.code_gen_service import code_gen_service
    except ImportError:
        raise cappa.Exit('Failed to import code generator plugin utilities; contact the system administrator', code=1)

    try:
        ids = []
        async with async_db_session() as db:
            results = await code_gen_business_service.get_all(db=db)

        if not results:
            raise cappa.Exit(
                '[red]No code generation business definitions available. Import them using the import command first![/]'
            )

        table = Table(show_header=True, header_style='bold magenta')
        table.add_column('Business definition number', style='cyan', no_wrap=True, justify='center')
        table.add_column('Application name', style='green', no_wrap=True)
        table.add_column('Output path', style='yellow')
        table.add_column('Notes', style='blue')

        for result in results:
            ids.append(result.id)
            table.add_row(
                str(result.id),
                result.app_name,
                result.gen_path or f'Root path of application {result.app_name}',
                result.remark or '',
            )

        console.print(table)
        business = IntPrompt.ask('Select a business definition number', choices=[str(id_) for id_ in ids])

        # Preview
        async with async_db_session() as db:
            preview_data = await code_gen_service.preview(db=db, pk=business)

        console.print('\n[bold yellow]The following files will be generated:[/]')
        file_table = Table(show_header=True, header_style='bold cyan')
        file_table.add_column('File path', style='white')
        file_table.add_column('Size', style='green', justify='right')

        for filepath, content in sorted(preview_data.items()):
            size = len(content)
            size_str = f'{size} B' if size < 1024 else f'{size / 1024:.1f} KB'
            file_table.add_row(filepath, size_str)

        console.print(file_table)

        if preview:
            console.print('\n[bold cyan]Preview mode: no files were generated[/]')
            return

        # Generate
        console.print(
            '\n[bold red]Warning: code generation writes to disk and overwrites files. Do not use in production![/]'
        )
        ok = Prompt.ask('\nContinue generating code?', choices=['y', 'n'], default='n')

        if ok.lower() == 'y':
            async with async_db_session.begin() as db:
                gen_path = await code_gen_service.generate(db=db, pk=business)

            console.print()
            console.tip('Code generated successfully')
            console.print(Text('\nFor details, see: '), Text(str(gen_path), style='bold white'))

    except Exception as e:
        raise cappa.Exit(e.msg if isinstance(e, BaseExceptionError) else str(e), code=1)


def run_alembic(*args: str) -> None:
    """Execute Alembic command"""
    try:
        subprocess.run(['alembic', *args], cwd=BASE_PATH.parent, check=True)
    except subprocess.CalledProcessError as e:
        raise cappa.Exit('Alembic command failed', code=e.returncode)


@cappa.command(help='Initialize FBA project', default_long=True)
@dataclass
class Init:
    auto: Annotated[
        bool,
        cappa.Arg(
            default=False,
            help=(
                'Automatic initialization: create .env, install dependencies, create the database, '
                'and initialize the schema'
            ),
        ),
    ]

    async def __call__(self) -> None:
        if self.auto:
            await auto_init()
        else:
            async with async_db_session.begin() as db:
                await init(db, redis_client)


@cappa.command(help='Run API service', default_long=True)
@dataclass
class Run:
    host: Annotated[
        str,
        cappa.Arg(
            default='127.0.0.1',
            help='Host IP address to serve on; use `127.0.0.1` for local development.'
            'Use `0.0.0.0` to allow external access, such as over a local network',
        ),
    ]
    port: Annotated[
        int,
        cappa.Arg(default=8000, help='Host port to serve on'),
    ]
    no_reload: Annotated[
        bool,
        cappa.Arg(default=False, help='Disable automatic server reload when code files change'),
    ]
    workers: Annotated[
        int,
        cappa.Arg(default=1, help='Use multiple worker processes; requires `--no-reload`'),
    ]

    def __call__(self) -> None:
        run(host=self.host, port=self.port, reload=self.no_reload, workers=self.workers)


@cappa.command(help='Add plugin', default_long=True)
@dataclass
class Add:
    path: Annotated[
        str | None,
        cappa.Arg(default=None, help='Full local path to the plugin ZIP archive'),
    ]
    repo_url: Annotated[
        str | None,
        cappa.Arg(default=None, help='Git repository URL of the plugin'),
    ]
    frontend: Annotated[
        bool,
        cappa.Arg(short='-f', default=False, help='Install frontend plugin'),
    ]
    no_sql: Annotated[
        bool,
        cappa.Arg(default=False, help='Disable automatic execution of plugin SQL scripts'),
    ]
    db_type: Annotated[
        DataBaseType,
        cappa.Arg(default=settings.DATABASE_TYPE, help='Database type for plugin SQL scripts'),
    ]
    pk_type: Annotated[
        PrimaryKeyType,
        cappa.Arg(default=settings.DATABASE_PK_MODE, help='Database primary key type for plugin SQL scripts'),
    ]

    async def __call__(self) -> None:
        await install_plugin(self.path, self.repo_url, self.frontend, self.no_sql, self.db_type, self.pk_type)


@cappa.command(help='Remove plugin')
@dataclass
class Remove:
    plugin: Annotated[
        str | None,
        cappa.Arg(default=None, help='Name of the plugin to remove'),
    ]
    no_sql: Annotated[
        bool,
        cappa.Arg(default=False, help='Disable automatic execution of plugin teardown SQL scripts'),
    ]

    async def __call__(self) -> None:
        await remove_plugin(self.plugin, no_sql=self.no_sql)


@cappa.command(help='Synchronize project and plugin dependencies', default_long=True)
@dataclass
class Deps:
    plugin: Annotated[
        str | None,
        cappa.Arg(default=None, help='Specify a plugin name; otherwise synchronize dependencies for all plugins'),
    ]
    no_project: Annotated[
        bool,
        cappa.Arg(default=False, help='Skip project dependency synchronization'),
    ]
    no_plugin: Annotated[
        bool,
        cappa.Arg(default=False, help='Skip plugin dependency synchronization'),
    ]

    async def __call__(self) -> None:
        await sync_deps(self.plugin, no_project=self.no_project, no_plugin=self.no_plugin)


@cappa.command(help='Format code')
@dataclass
class Format:
    def __call__(self) -> None:
        try:
            subprocess.run(['prek', 'run', '--all-files'], cwd=BASE_PATH.parent, check=False)
        except FileNotFoundError:
            raise cappa.Exit('prek is not installed; install project dependencies first', code=1)
        except KeyboardInterrupt:
            pass


@cappa.command(help='Start Celery worker service on the current host', default_long=True)
@dataclass
class Worker:
    log_level: Annotated[
        Literal['info', 'debug'],
        cappa.Arg(short='-l', default='info', help='Log output level'),
    ]

    def __call__(self) -> None:
        run_celery_worker(log_level=self.log_level)


@cappa.command(help='Start Celery beat service on the current host', default_long=True)
@dataclass
class Beat:
    log_level: Annotated[
        Literal['info', 'debug'],
        cappa.Arg(short='-l', default='info', help='Log output level'),
    ]

    def __call__(self) -> None:
        run_celery_beat(log_level=self.log_level)


@cappa.command(help='Start Celery Flower service on the current host', default_long=True)
@dataclass
class Flower:
    port: Annotated[
        int,
        cappa.Arg(default=8555, help='Host port to serve on'),
    ]
    basic_auth: Annotated[
        str,
        cappa.Arg(default='admin:123456', help='Username and password for the web interface'),
    ]

    def __call__(self) -> None:
        run_celery_flower(port=self.port, basic_auth=self.basic_auth)


@cappa.command(help='Run Celery service')
@dataclass
class Celery:
    subcmd: cappa.Subcommands[Worker | Beat | Flower]


@cappa.command(help='Import code generation business definitions and model columns', default_long=True)
@dataclass
class Import:
    app: Annotated[
        str,
        cappa.Arg(help='Application name identifying the app in which to generate code'),
    ]
    table_schema: Annotated[
        str,
        cappa.Arg(short='tc', default='fba', help='Database name'),
    ]
    table_name: Annotated[
        str,
        cappa.Arg(short='tn', help='Database table name'),
    ]

    async def __call__(self) -> None:
        await import_table(self.app, self.table_schema, self.table_name)


@cappa.command(
    name='codegen',
    help='Code generation (deploy the FBA vben frontend project for full functionality)',
    default_long=True,
)
@dataclass
class CodeGenerator:
    preview: Annotated[
        bool,
        cappa.Arg(short='-p', default=False, help='Preview the files to be generated without writing them'),
    ]
    subcmd: cappa.Subcommands[Import | None] = None

    async def __call__(self) -> None:
        await generate(preview=self.preview)


@cappa.command(help='Generate database migration file', default_long=True)
@dataclass
class Revision:
    autogenerate: Annotated[
        bool,
        cappa.Arg(default=True, help='Automatically detect model changes and generate a migration script'),
    ]
    message: Annotated[
        str,
        cappa.Arg(short='-m', default='', help='Migration description'),
    ]

    def __call__(self) -> None:
        args = ['revision']
        if self.autogenerate:
            args.append('--autogenerate')
        if self.message:
            args.extend(['-m', self.message])
        run_alembic(*args)
        console.tip('Migration file generated successfully')


@cappa.command(help='Upgrade database to the specified revision', default_long=True)
@dataclass
class Upgrade:
    revision: Annotated[
        str,
        cappa.Arg(default='head', help='Target revision; defaults to the latest revision'),
    ]

    def __call__(self) -> None:
        run_alembic('upgrade', self.revision)
        console.tip(f'Database upgraded to: {self.revision}')


@cappa.command(help='Downgrade database to the specified revision', default_long=True)
@dataclass
class Downgrade:
    revision: Annotated[
        str,
        cappa.Arg(default='-1', help='Target revision; defaults to one revision back'),
    ]

    def __call__(self) -> None:
        run_alembic('downgrade', self.revision)
        console.tip(f'Database downgraded to: {self.revision}')


@cappa.command(help='Show current database migration revision')
@dataclass
class Current:
    verbose: Annotated[
        bool,
        cappa.Arg(short='-v', default=False, help='Show detailed information'),
    ]

    def __call__(self) -> None:
        args = ['current']
        if self.verbose:
            args.append('-v')
        run_alembic(*args)


@cappa.command(help='Show migration history', default_long=True)
@dataclass
class History:
    verbose: Annotated[
        bool,
        cappa.Arg(short='-v', default=False, help='Show detailed information'),
    ]
    range: Annotated[
        str,
        cappa.Arg(short='-r', default='', help='Show history within a range, such as -r base:head'),
    ]

    def __call__(self) -> None:
        args = ['history']
        if self.verbose:
            args.append('-v')
        if self.range:
            args.extend(['-r', self.range])
        run_alembic(*args)


@cappa.command(help='Show all head revisions')
@dataclass
class Heads:
    verbose: Annotated[
        bool,
        cappa.Arg(short='-v', default=False, help='Show detailed information'),
    ]

    def __call__(self) -> None:
        args = ['heads']
        if self.verbose:
            args.append('-v')
        run_alembic(*args)


@cappa.command(help='Database migration management')
@dataclass
class Alembic:
    subcmd: cappa.Subcommands[Revision | Upgrade | Downgrade | Current | History | Heads]


@cappa.command(help='An efficient command-line interface for FBA', default_long=True)
@dataclass
class FbaCli:
    sql: Annotated[
        str,
        cappa.Arg(value_name='PATH', default='', show_default=False, help='Execute SQL scripts in a transaction'),
    ]
    subcmd: cappa.Subcommands[Init | Run | Add | Remove | Deps | Format | Celery | CodeGenerator | Alembic | None] = (
        None
    )

    async def __call__(self) -> None:
        if self.sql:
            async with async_db_session.begin() as db:
                await execute_sql_scripts(db, self.sql)


def main() -> None:
    output = cappa.Output(error_format=f'{error_format}\n{_OUTPUT_HELP}')
    asyncio.run(cappa.invoke_async(FbaCli, version=__version__, output=output))
