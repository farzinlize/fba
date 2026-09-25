from fastapi import Request

from backend.common.exception import errors
from backend.core.conf import settings


async def demo_site(request: Request) -> None:  # ruff:ignore[unused-async]
    """
    Demo site

    :param request: FastAPI request object
    :return:
    """
    method = request.method
    path = request.url.path
    if (
        settings.DEMO_MODE
        and method != 'GET'
        and method != 'OPTIONS'
        and (method, path) not in settings.DEMO_MODE_EXCLUDE
    ):
        raise errors.ForbiddenError(msg='This operation is prohibited in the demo environment')
