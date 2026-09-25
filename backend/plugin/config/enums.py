from backend.common.enums import StrEnum


class ConfigType(StrEnum):
    """Configuration type"""

    ai = 'AI'
    email = 'EMAIL'
    user_security = 'USER_SECURITY'
    login = 'LOGIN'
