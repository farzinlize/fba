from typing import Any

from opentelemetry import trace
from starlette.requests import Request
from starlette_context.plugins import Plugin

from backend.common.context import ctx
from backend.core.conf import settings


def get_request_trace_id() -> str:
    """Get trace ID from context"""
    if ctx.exists():
        return ctx.get(settings.TRACE_ID_REQUEST_HEADER_KEY, settings.TRACE_ID_LOG_DEFAULT_VALUE)
    return settings.TRACE_ID_LOG_DEFAULT_VALUE


class OtelTraceIdPlugin(Plugin):
    """OpenTelemetry Trace ID plugin"""

    key = settings.TRACE_ID_REQUEST_HEADER_KEY

    async def process_request(self, request: Request) -> Any:
        """Extract trace_id from an OpenTelemetry span"""
        span = trace.get_current_span()
        span_ctx = span.get_span_context()

        if span_ctx.is_valid:
            return trace.format_trace_id(span_ctx.trace_id)

        return settings.TRACE_ID_LOG_DEFAULT_VALUE
