from typing import Any

from fastapi import HTTPException
from starlette.background import BackgroundTask

from backend.common.response.response_code import CustomErrorCode, StandardResponseCode


class BaseExceptionError(Exception):
    """Base exception mixin"""

    code: int

    def __init__(self, *, msg: str | None = None, data: Any = None, background: BackgroundTask | None = None) -> None:
        self.msg = msg
        self.data = data
        # The original background task: https://www.starlette.io/background/
        self.background = background
        super().__init__(msg)


class HTTPError(HTTPException):
    """HTTP exception"""

    def __init__(self, *, code: int, msg: Any = None, headers: dict[str, Any] | None = None) -> None:
        super().__init__(status_code=code, detail=msg, headers=headers)


class CustomError(BaseExceptionError):
    """Custom exception"""

    def __init__(self, *, error: CustomErrorCode, data: Any = None, background: BackgroundTask | None = None) -> None:
        self.code = error.code
        super().__init__(msg=error.msg, data=data, background=background)


class RequestError(BaseExceptionError):
    """Request exception"""

    def __init__(
        self,
        *,
        code: int = StandardResponseCode.HTTP_400,
        msg: str = 'Bad Request',
        data: Any = None,
        background: BackgroundTask | None = None,
    ) -> None:
        self.code = code
        super().__init__(msg=msg, data=data, background=background)


class ForbiddenError(BaseExceptionError):
    """Access forbidden exception"""

    code = StandardResponseCode.HTTP_403

    def __init__(self, *, msg: str = 'Forbidden', data: Any = None, background: BackgroundTask | None = None) -> None:
        super().__init__(msg=msg, data=data, background=background)


class NotFoundError(BaseExceptionError):
    """Resource not found exception"""

    code = StandardResponseCode.HTTP_404

    def __init__(self, *, msg: str = 'Not Found', data: Any = None, background: BackgroundTask | None = None) -> None:
        super().__init__(msg=msg, data=data, background=background)


class ServerError(BaseExceptionError):
    """Server exception"""

    code = StandardResponseCode.HTTP_500

    def __init__(
        self,
        *,
        msg: str = 'Internal Server Error',
        data: Any = None,
        background: BackgroundTask | None = None,
    ) -> None:
        super().__init__(msg=msg, data=data, background=background)


class GatewayError(BaseExceptionError):
    """Gateway exception"""

    code = StandardResponseCode.HTTP_502

    def __init__(self, *, msg: str = 'Bad Gateway', data: Any = None, background: BackgroundTask | None = None) -> None:
        super().__init__(msg=msg, data=data, background=background)


class AuthorizationError(BaseExceptionError):
    """Authentication exception"""

    code = StandardResponseCode.HTTP_403

    def __init__(
        self,
        *,
        msg: str = 'Permission Denied',
        data: Any = None,
        background: BackgroundTask | None = None,
    ) -> None:
        super().__init__(msg=msg, data=data, background=background)


class TokenError(HTTPError):
    """Token exception"""

    code = StandardResponseCode.HTTP_401

    def __init__(self, *, msg: str = 'Not Authenticated', headers: dict[str, Any] | None = None) -> None:
        super().__init__(code=self.code, msg=msg, headers=headers or {'WWW-Authenticate': 'Bearer'})


class ConflictError(BaseExceptionError):
    """Resource conflict exception"""

    code = StandardResponseCode.HTTP_409

    def __init__(self, *, msg: str = 'Conflict', data: Any = None, background: BackgroundTask | None = None) -> None:
        super().__init__(msg=msg, data=data, background=background)
