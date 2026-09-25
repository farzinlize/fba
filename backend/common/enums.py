from enum import Enum
from enum import IntEnum as SourceIntEnum
from typing import Any, TypeVar

T = TypeVar('T', bound=Enum)


class _EnumBase:
    """Base enum providing common methods"""

    @classmethod
    def get_member_keys(cls) -> list[str]:
        """Get enum member names"""
        return list(cls.__members__.keys())

    @classmethod
    def get_member_values(cls) -> list:
        """Get enum member values"""
        return [item.value for item in cls.__members__.values()]

    @classmethod
    def get_member_dict(cls) -> dict[str, Any]:
        """Get enum member dictionary"""
        return {name: item.value for name, item in cls.__members__.items()}


class IntEnum(_EnumBase, SourceIntEnum):
    """Integer enum base class"""


class StrEnum(_EnumBase, str, Enum):
    """String enum base class"""


class MenuType(IntEnum):
    """Menu type"""

    directory = 0
    menu = 1
    button = 2
    embedded = 3
    link = 4


class RoleDataRuleOperatorType(IntEnum):
    """Data rule operator"""

    AND = 0
    OR = 1


class RoleDataRuleExpressionType(IntEnum):
    """Data rule expression"""

    eq = 0  # ==
    ne = 1  # !=
    gt = 2  # >
    ge = 3  # >=
    lt = 4  # <
    le = 5  # <=
    in_ = 6
    not_in = 7


class MethodType(StrEnum):
    """HTTP request method"""

    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'
    OPTIONS = 'OPTIONS'


class LoginLogStatusType(IntEnum):
    """Login log status"""

    fail = 0
    success = 1


class BuildTreeType(StrEnum):
    """Tree structure type"""

    traversal = 'traversal'
    recursive = 'recursive'


class OperaLogCipherType(IntEnum):
    """Operation log encryption type"""

    aes = 0
    md5 = 1
    itsdangerous = 2
    plain = 3


class StatusType(IntEnum):
    """Status type"""

    disable = 0
    enable = 1


class FileType(StrEnum):
    """File type"""

    image = 'image'
    video = 'video'


class PluginLevelType(StrEnum):
    """Plugin level type"""

    app = 'app'
    capability = 'capability'
    extend = 'extend'


class PluginType(StrEnum):
    """Plugin type"""

    zip = 'zip'
    git = 'git'


class UserPermissionType(StrEnum):
    """User permission type"""

    superuser = 'superuser'
    staff = 'staff'
    status = 'status'
    multi_login = 'multi_login'


class DataBaseType(StrEnum):
    """Database type"""

    mysql = 'mysql'
    postgresql = 'postgresql'


class PrimaryKeyType(StrEnum):
    """Primary key type"""

    autoincrement = 'autoincrement'
    snowflake = 'snowflake'


class LifespanStage(IntEnum):
    """Lifespan execution phase"""

    core = 0
    plugin = 1
    tail = 2
