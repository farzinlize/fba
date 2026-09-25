from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from uvicorn.protocols.http.h11_impl import STATUS_PHRASES

from backend.common.context import ctx
from backend.common.exception.errors import BaseExceptionError
from backend.common.i18n import i18n, t
from backend.common.response.response_code import CustomResponseCode, StandardResponseCode
from backend.common.response.response_schema import response_base
from backend.core.conf import settings
from backend.utils.serializers import MsgSpecJSONResponse
from backend.utils.trace_id import get_request_trace_id


def _get_exception_code(status_code: int) -> int:
    """
    Get response status code (available codes are defined by RFCs)

    `Python standard status codes <https://github.com/python/cpython/blob/6e3cc72afeaee2532b4327776501eb8234ac787b/Lib/http/__init__.py#L7>`__

    `IANA status code registry <https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml>`__

    :param status_code: HTTP status code
    :return:
    """
    try:
        STATUS_PHRASES[status_code]
    except Exception:
        return StandardResponseCode.HTTP_400

    return status_code


async def _validation_exception_handler(exc: RequestValidationError | ValidationError):
    """
    Handle data validation errors

    :param exc: Validation error
    :return:
    """
    errors = []
    for error in exc.errors():
        # Use custom error messages for languages other than en-US
        if i18n.current_language != 'en-US':
            custom_message = t(f'pydantic.{error["type"]}')
            if custom_message:
                error_ctx = error.get('ctx') or {}
                error['msg'] = custom_message.format(**error_ctx)
                e = error_ctx.get('error')
                if isinstance(e, Exception):
                    error['ctx']['error'] = str(e).replace("'", '"')
        errors.append(error)
    error = errors[0]
    if error.get('type') == 'json_invalid':
        message = 'JSON parsing failed'
    else:
        error_input = error.get('input')
        field = str(error.get('loc')[-1])
        error_msg = error.get('msg')
        message = f'{field} {error_msg}; input: {error_input}' if settings.ENVIRONMENT == 'dev' else error_msg
    msg = f'Invalid request parameters: {message}'
    data = {'errors': errors} if settings.ENVIRONMENT == 'dev' else None
    content = {
        'code': StandardResponseCode.HTTP_422,
        'msg': msg,
        'data': data,
    }
    ctx.__request_validation_exception__ = content  # Retrieve exception information in middleware
    content.update(trace_id=get_request_trace_id())
    return MsgSpecJSONResponse(status_code=StandardResponseCode.HTTP_422, content=content)


def register_exception(app: FastAPI) -> None:  # ruff:ignore[complex-structure]
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Global HTTP exception handler

        :param request: FastAPI request object
        :param exc: HTTP exception
        :return:
        """
        if settings.ENVIRONMENT == 'dev':
            content = {
                'code': exc.status_code,
                'msg': exc.detail,
                'data': None,
            }
        else:
            res = response_base.fail(res=CustomResponseCode.HTTP_400)
            content = res.model_dump()
        ctx.__request_http_exception__ = content
        content.update(trace_id=get_request_trace_id())
        return MsgSpecJSONResponse(
            status_code=_get_exception_code(exc.status_code),
            content=content,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def fastapi_validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        FastAPI data validation exception handler

        :param request: FastAPI request object
        :param exc: Validation error
        :return:
        """
        return await _validation_exception_handler(exc)

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """
        Pydantic data validation exception handler

        :param request: Request object
        :param exc: Validation error
        :return:
        """
        return await _validation_exception_handler(exc)

    @app.exception_handler(AssertionError)
    async def assertion_error_handler(request: Request, exc: AssertionError):
        """
        Assertion error handler

        :param request: FastAPI request object
        :param exc: Assertion error
        :return:
        """
        if settings.ENVIRONMENT == 'dev':
            content = {
                'code': StandardResponseCode.HTTP_500,
                'msg': str(''.join(exc.args) if exc.args else exc.__doc__),
                'data': None,
            }
        else:
            res = response_base.fail(res=CustomResponseCode.HTTP_500)
            content = res.model_dump()
        ctx.__request_assertion_error__ = content
        content.update(trace_id=get_request_trace_id())
        return MsgSpecJSONResponse(
            status_code=StandardResponseCode.HTTP_500,
            content=content,
        )

    @app.exception_handler(BaseExceptionError)
    async def custom_exception_handler(request: Request, exc: BaseExceptionError):
        """
        Global custom exception handler

        :param request: FastAPI request object
        :param exc: Custom exception
        :return:
        """
        content = {
            'code': exc.code,
            'msg': str(exc.msg),
            'data': exc.data or None,
        }
        ctx.__request_custom_exception__ = content
        content.update(trace_id=get_request_trace_id())
        return MsgSpecJSONResponse(
            status_code=_get_exception_code(exc.code),
            content=content,
            background=exc.background,
        )

    @app.exception_handler(Exception)
    async def all_unknown_exception_handler(request: Request, exc: Exception):
        """
        Global unknown exception handler

        :param request: FastAPI request object
        :param exc: Unknown exception
        :return:
        """
        if settings.ENVIRONMENT == 'dev':
            content = {
                'code': StandardResponseCode.HTTP_500,
                'msg': str(exc),
                'data': None,
            }
        else:
            res = response_base.fail(res=CustomResponseCode.HTTP_500)
            content = res.model_dump()
        ctx.__request_unknown_exception__ = content
        content.update(trace_id=get_request_trace_id())
        return MsgSpecJSONResponse(
            status_code=StandardResponseCode.HTTP_500,
            content=content,
        )

    if settings.MIDDLEWARE_CORS:

        @app.exception_handler(StandardResponseCode.HTTP_500)
        async def cors_custom_code_500_exception_handler(request: Request, exc: BaseExceptionError | Exception):
            """
            Custom CORS-aware 500 error handler

            :param request: FastAPI request object
            :param exc: Custom exception
            :return:
            """
            if isinstance(exc, BaseExceptionError):
                content = {
                    'code': exc.code,
                    'msg': exc.msg,
                    'data': exc.data,
                }
            else:
                if settings.ENVIRONMENT == 'dev':
                    content = {
                        'code': StandardResponseCode.HTTP_500,
                        'msg': str(exc),
                        'data': None,
                    }
                else:
                    res = response_base.fail(res=CustomResponseCode.HTTP_500)
                    content = res.model_dump()
            if isinstance(exc, BaseExceptionError):
                ctx.__request_custom_exception__ = content
            else:
                ctx.__request_unknown_exception__ = content
            content.update(trace_id=get_request_trace_id())
            response = MsgSpecJSONResponse(
                status_code=exc.code if isinstance(exc, BaseExceptionError) else StandardResponseCode.HTTP_500,
                content=content,
                background=exc.background if isinstance(exc, BaseExceptionError) else None,
            )
            origin = request.headers.get('origin')
            if origin:
                cors = CORSMiddleware(
                    app=app,
                    allow_origins=settings.CORS_ALLOWED_ORIGINS,
                    allow_credentials=True,
                    allow_methods=['*'],
                    allow_headers=['*'],
                    expose_headers=settings.CORS_EXPOSE_HEADERS,
                )
                response.headers.update(cors.simple_headers)
                has_cookie = 'cookie' in request.headers
                if cors.allow_all_origins and has_cookie:
                    response.headers['Access-Control-Allow-Origin'] = origin
                elif not cors.allow_all_origins and cors.is_allowed_origin(origin=origin):
                    response.headers['Access-Control-Allow-Origin'] = origin
                    response.headers.add_vary_header('Origin')
            return response
