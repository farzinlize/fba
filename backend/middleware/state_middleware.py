from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.common.context import ctx
from backend.utils.request_parse import parse_ip_info, parse_user_agent_info


class StateMiddleware(BaseHTTPMiddleware):
    """Request state middleware"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process request and set request state information

        :param request: FastAPI request object
        :param call_next: Next middleware or route handler
        :return:
        """
        ip_info = await parse_ip_info(request)
        ctx.ip = ip_info.ip
        ctx.country = ip_info.country
        ctx.region = ip_info.region
        ctx.city = ip_info.city

        ua_info = parse_user_agent_info(request)
        ctx.user_agent = ua_info.user_agent
        ctx.os = ua_info.os
        ctx.browser = ua_info.browser
        ctx.device = ua_info.device

        response = await call_next(request)

        return response
