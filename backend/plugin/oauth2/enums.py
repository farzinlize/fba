from backend.common.enums import StrEnum


class UserSocialType(StrEnum):
    """User social account type"""

    github = 'Github'
    google = 'Google'


class UserSocialAuthType(StrEnum):
    """User social authorization type"""

    login = 'login'
    binding = 'binding'
