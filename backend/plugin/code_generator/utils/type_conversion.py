from functools import lru_cache

from backend.common.enums import DataBaseType
from backend.core.conf import settings
from backend.plugin.code_generator.enums import GenMySQLColumnType, GenPostgreSQLColumnType


@lru_cache(maxsize=128)
def sql_type_to_sqlalchemy(typing: str) -> str:
    """
    Convert SQL type to SQLAlchemy type

    :param typing: SQL type string
    :return:
    """
    if DataBaseType.mysql == settings.DATABASE_TYPE:
        if typing in GenMySQLColumnType.get_member_keys():
            return typing
    else:
        normalized_type = typing.replace(' ', '_')
        if normalized_type in GenPostgreSQLColumnType.get_member_keys():
            return typing
    return 'String'


@lru_cache(maxsize=128)
def sql_type_to_pydantic(typing: str) -> str:
    """
    Convert SQL type to Pydantic type

    :param typing: SQL type string
    :return:
    """
    try:
        if DataBaseType.mysql == settings.DATABASE_TYPE:
            return GenMySQLColumnType[typing].value
        normalized_type = typing.replace(' ', '_')
        return GenPostgreSQLColumnType[normalized_type].value
    except KeyError:
        return 'str'


@lru_cache(maxsize=128)
def sql_type_to_sqlalchemy_name(typing: str) -> str:
    """
    Convert SQL type to a valid SQLAlchemy type name for code generation

    :param typing: SQL type string
    :return:
    """
    pg_type_mapping = {
        'CHARACTER VARYING': 'String',
        'CHARACTER': 'CHAR',
        'TIMESTAMP WITHOUT TIME ZONE': 'TIMESTAMP',
        'TIMESTAMP WITH TIME ZONE': 'TIMESTAMP',
        'TIME WITHOUT TIME ZONE': 'TIME',
        'TIME WITH TIME ZONE': 'TIME',
        'DOUBLE PRECISION': 'Double',
    }

    if DataBaseType.postgresql == settings.DATABASE_TYPE and typing in pg_type_mapping:
        return pg_type_mapping[typing]

    return typing
