from pathlib import Path
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.common.enums import PluginLevelType
from backend.core.path_conf import PLUGIN_DIR
from backend.plugin.errors import PluginConfigError
from backend.utils.pattern_validate import match_string

# Supported tag types
_VALID_TAGS: Final = frozenset({'ai', 'mcp', 'agent', 'auth', 'storage', 'notification', 'task', 'payment', 'other'})

# Supported database types
_VALID_DATABASES: Final = frozenset({'mysql', 'postgresql'})


def _validate_settings(v: dict[str, Any]) -> dict[str, Any]:
    """Validate plugin setting names and value types"""
    invalid_keys = [key for key in v if not key.isupper()]
    if invalid_keys:
        raise PluginConfigError(f'Setting names must be uppercase; invalid settings: {", ".join(invalid_keys)}')

    invalid_values = [
        key
        for key, value in v.items()
        if not isinstance(value, (str, int, float, bool))
        and not (isinstance(value, list) and all(isinstance(item, str) for item in value))
    ]
    if invalid_values:
        raise PluginConfigError(
            f'Setting values must be strings, numbers, booleans, or lists of strings; invalid '
            f'settings: {", ".join(invalid_values)}'
        )
    return v


class PluginInfoSchema(BaseModel):
    """Plugin information model"""

    icon: str | None = Field(None, description='Icon path or URL')
    summary: str = Field(..., min_length=1, max_length=100, description='Summary')
    version: str = Field(..., description='Version number')
    description: str = Field(..., min_length=1, max_length=500, description='Description')
    author: str = Field(..., min_length=1, max_length=50, description='Author')
    tags: list[str] = Field(..., min_length=1, description='Tags')
    database: list[str] = Field(..., min_length=1, description='Database support')
    depends_on: list[str] = Field(default_factory=list, description='List of plugin dependencies')

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version number format"""
        if not match_string(r'^\d+\.\d+\.\d+$', v):
            raise PluginConfigError(f'Invalid version format; expected x.y.z, such as 1.0.0; current value: {v}')
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags"""
        if v:
            invalid_tags = set(v) - _VALID_TAGS
            if invalid_tags:
                raise PluginConfigError(
                    f'Invalid tags: {", ".join(invalid_tags)}; supported tags: {", ".join(sorted(_VALID_TAGS))}'
                )
        return v

    @field_validator('database')
    @classmethod
    def validate_database(cls, v: list[str]) -> list[str]:
        """Validate database types"""
        if v:
            invalid_dbs = set(v) - _VALID_DATABASES
            if invalid_dbs:
                raise PluginConfigError(
                    f'Invalid database types: {", ".join(invalid_dbs)}; supported databases: '
                    f'{", ".join(sorted(_VALID_DATABASES))}'
                )
        return v

    @field_validator('depends_on')
    @classmethod
    def validate_depends_on(cls, v: list[str]) -> list[str]:
        """Validate plugin dependencies"""
        for dep in v:
            if not dep or not isinstance(dep, str):
                raise PluginConfigError(f'Plugin dependencies must be nonempty strings; current value: {dep}')
        return v


class CapabilityPluginInfoSchema(PluginInfoSchema):
    """Capability plugin information model"""

    database: list[str] = Field(default_factory=list, description='Database support')


class AppPluginAppSchema(BaseModel):
    """Application-level plugin app configuration model"""

    router: list[str] = Field(..., min_length=1, description='List of router instances')

    @field_validator('router')
    @classmethod
    def validate_router(cls, v: list[str]) -> list[str]:
        """Validate router configuration"""
        if not v:
            raise PluginConfigError('router configuration must not be empty')
        for router in v:
            if not router or not isinstance(router, str):
                raise PluginConfigError(f'router entries must be nonempty strings; current value: {router}')
        return v


class ExtendPluginAppSchema(BaseModel):
    """Extension-level plugin app configuration model"""

    extend: str = Field(..., min_length=1, description='Name of the application folder to extend')


class ApiConfigSchema(BaseModel):
    """API configuration model"""

    prefix: str = Field(..., min_length=1, description='Route prefix')
    tags: str = Field(..., min_length=1, description='Swagger documentation tags')

    @field_validator('prefix')
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        """Validate route prefix"""
        if not v.startswith('/'):
            raise PluginConfigError(f'Route prefix must start with "/"; current value: {v}')
        if not match_string(r'^/[a-zA-Z0-9_/-]*$', v):
            raise PluginConfigError(
                f'Route prefix may only contain letters, digits, underscores, slashes, and hyphens; current value: {v}'
            )
        return v


class AppPluginConfigSchema(BaseModel):
    """Application-level plugin configuration model"""

    plugin: PluginInfoSchema = Field(..., description='Plugin information')
    app: AppPluginAppSchema = Field(..., description='Application configuration')
    settings: dict[str, Any] = Field(default_factory=dict, description='Settings')

    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate settings"""
        return _validate_settings(v)


class ExtendPluginConfigSchema(BaseModel):
    """Extension-level plugin configuration model"""

    plugin: PluginInfoSchema = Field(..., description='Plugin information')
    app: ExtendPluginAppSchema = Field(..., description='Application configuration')
    api: dict[str, ApiConfigSchema] = Field(..., min_length=1, description='API configuration')
    settings: dict[str, Any] = Field(default_factory=dict, description='Settings')

    @field_validator('api', mode='before')
    @classmethod
    def validate_api_config(cls, v: dict[str, Any]) -> dict[str, ApiConfigSchema]:
        """Validate and convert API configuration"""
        if not v:
            raise PluginConfigError('Extension-level plugins must include at least one API configuration')
        validated_api = {}
        for api_name, api_config in v.items():
            if not api_name or not isinstance(api_name, str):
                raise PluginConfigError(f'API configuration names must be nonempty strings; current value: {api_name}')
            if not match_string(r'^[a-zA-Z_][a-zA-Z0-9_]*$', api_name):
                raise PluginConfigError(
                    f'API configuration names must start with a letter or underscore and contain only '
                    f'letters, digits, and underscores; current value: {api_name}'
                )
            validated_api[api_name] = ApiConfigSchema(**api_config) if isinstance(api_config, dict) else api_config
        return validated_api

    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate settings"""
        return _validate_settings(v)


class CapabilityPluginConfigSchema(BaseModel):
    """Capability plugin configuration model"""

    model_config = ConfigDict(extra='forbid')

    plugin: CapabilityPluginInfoSchema = Field(..., description='Plugin information')
    settings: dict[str, Any] = Field(default_factory=dict, description='Settings')

    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate settings"""
        return _validate_settings(v)


def validate_plugin_config(plugin_name: str, config: dict[str, Any]) -> PluginLevelType:
    """
    Validate plugin configuration

    :param plugin_name: Plugin name
    :param config: Plugin configuration dictionary
    :return:
    """
    plugin_schema, plugin_level = (
        (ExtendPluginConfigSchema, PluginLevelType.extend)
        if 'api' in config
        else (AppPluginConfigSchema, PluginLevelType.app)
        if 'app' in config
        else (CapabilityPluginConfigSchema, PluginLevelType.capability)
    )

    try:
        plugin_schema.model_validate(config)
    except Exception as e:
        error_msg = str(e)
        # Format Pydantic error messages
        if hasattr(e, 'errors'):
            errors = e.errors()
            error_details = []
            for error in errors:
                loc = '.'.join(str(loc) for loc in error['loc'])
                msg = error['msg']
                error_details.append(f'{loc}: {msg}')
            error_msg = '; '.join(error_details)
        raise PluginConfigError(f'Configuration validation failed for plugin {plugin_name}: {error_msg}') from e

    depends_on = config['plugin'].get('depends_on', [])
    if plugin_name in depends_on:
        raise PluginConfigError(f'Plugin {plugin_name} cannot depend on itself')

    plugin_dir = Path(PLUGIN_DIR) / plugin_name
    model_dir = plugin_dir / 'model'
    if model_dir.is_dir():
        if not config['plugin'].get('database'):
            raise PluginConfigError(
                f'Plugin {plugin_name} must declare supported databases when it includes a model directory'
            )

        sql_dir = plugin_dir / 'sql'
        supported_db_types = []
        missing_details = []

        for db_type in ('mysql', 'postgresql'):
            db_sql_dir = sql_dir / db_type
            required_sql_files = (
                db_sql_dir / 'init.sql',
                db_sql_dir / 'destroy.sql',
                db_sql_dir / 'init_snowflake.sql',
                db_sql_dir / 'destroy_snowflake.sql',
            )
            missing_files = [
                str(sql_file.relative_to(plugin_dir)) for sql_file in required_sql_files if not sql_file.is_file()
            ]

            if not missing_files:
                supported_db_types.append(db_type)
                continue

            missing_details.append(f'{db_type}: {", ".join(missing_files)}')

        if not supported_db_types:
            raise PluginConfigError(
                f'Plugin {plugin_name} must provide initialization and teardown SQL scripts for at '
                f'least one database; missing: {"; ".join(missing_details)}'
            )

    return plugin_level
