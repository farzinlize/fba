from pydantic import Field

from backend.common.schema import SchemaBase


class GetCaptchaDetail(SchemaBase):
    """CAPTCHA details"""

    is_enabled: bool = Field(description='Enabled')
    expire_seconds: int = Field(description='Expiration in seconds')
    uuid: str = Field(description='Unique image identifier')
    image: str = Field(description='Image content')
