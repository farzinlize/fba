from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.cache.decorator import cache_invalidate, cached
from backend.common.exception import errors
from backend.common.pagination import paging_data
from backend.core.conf import settings
from backend.plugin.config.crud.crud_config import config_dao
from backend.plugin.config.model import Config
from backend.plugin.config.schema.config import (
    CreateConfigParam,
    UpdateConfigParam,
    UpdateConfigsParam,
)


class ConfigService:
    """Configuration parameter service"""

    @staticmethod
    @cached(namespace=settings.CACHE_CONFIG_REDIS_PREFIX, key='pk')
    async def get(*, db: AsyncSession, pk: int) -> Config:
        """
        Get configuration parameter details

        :param db: Database session
        :param pk: Configuration parameter ID
        :return:
        """
        config = await config_dao.get(db, pk)
        if not config:
            raise errors.NotFoundError(msg='Configuration parameter does not exist')
        return config

    @staticmethod
    @cached(namespace=settings.CACHE_CONFIG_REDIS_PREFIX, key='type')
    async def get_all(*, db: AsyncSession, type: str | None) -> Sequence[Config | None]:
        """
        Get all configuration parameters

        :param db: Database session
        :param type: Configuration parameter type
        :return:
        """
        return await config_dao.get_all(db, type)

    @staticmethod
    async def get_list(*, db: AsyncSession, name: str | None, type: str | None) -> dict[str, Any]:
        """
        Get configuration parameter list

        :param db: Database session
        :param name: Configuration parameter name
        :param type: Configuration parameter type
        :return:
        """
        config_select = await config_dao.get_select(name=name, type=type)
        return await paging_data(db, config_select)

    @staticmethod
    @cache_invalidate(namespace=settings.CACHE_CONFIG_REDIS_PREFIX)
    async def create(*, db: AsyncSession, obj: CreateConfigParam) -> None:
        """
        Create configuration parameter

        :param db: Database session
        :param obj: Configuration parameter creation parameters
        :return:
        """
        config = await config_dao.get_by_key(db, obj.key)
        if config:
            raise errors.ConflictError(msg=f'Configuration parameter {obj.key} already exists')
        await config_dao.create(db, obj)

    @staticmethod
    @cache_invalidate(namespace=settings.CACHE_CONFIG_REDIS_PREFIX)
    async def update(*, db: AsyncSession, pk: int, obj: UpdateConfigParam) -> int:
        """
        Update configuration parameter

        :param db: Database session
        :param pk: Configuration parameter ID
        :param obj: Configuration parameter update parameters
        :return:
        """
        config = await config_dao.get(db, pk)
        if not config:
            raise errors.NotFoundError(msg='Configuration parameter does not exist')
        if config.key != obj.key:
            config = await config_dao.get_by_key(db, obj.key)
            if config:
                raise errors.ConflictError(msg=f'Configuration parameter {obj.key} already exists')
        count = await config_dao.update(db, pk, obj)
        return count

    @staticmethod
    @cache_invalidate(namespace=settings.CACHE_CONFIG_REDIS_PREFIX)
    async def bulk_update(*, db: AsyncSession, objs: list[UpdateConfigsParam]) -> int:
        """
        Update configuration parameters in bulk

        :param db: Database session
        :param objs: Bulk configuration parameter update parameters
        :return:
        """
        configs = await config_dao.get_all_by_ids(db, list({obj.id for obj in objs}))
        config_map = {config.id: config for config in configs}
        for obj in objs:
            if obj.id not in config_map:
                raise errors.NotFoundError(msg='Configuration parameter does not exist')

        changed_keys = [obj.key for obj in objs if config_map[obj.id].key != obj.key]
        if len(changed_keys) != len(set(changed_keys)):
            raise errors.ConflictError(msg='Duplicate configuration parameter key')

        key_configs = await config_dao.get_all_by_keys(db, list(set(changed_keys)))
        key_owner = {config.key: config.id for config in key_configs}
        for obj in objs:
            if config_map[obj.id].key != obj.key and obj.key in key_owner and key_owner[obj.key] != obj.id:
                raise errors.ConflictError(msg=f'Configuration parameter {obj.key} already exists')

        count = await config_dao.bulk_update(db, objs)
        return count

    @staticmethod
    @cache_invalidate(namespace=settings.CACHE_CONFIG_REDIS_PREFIX)
    async def delete(*, db: AsyncSession, pks: list[int]) -> int:
        """
        Delete configuration parameters in bulk

        :param db: Database session
        :param pks: Configuration parameter ID list
        :return:
        """
        count = await config_dao.delete(db, pks)
        return count


config_service: ConfigService = ConfigService()
