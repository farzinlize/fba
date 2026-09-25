from fastapi import FastAPI
from starlette.middleware import Middleware


def replace_middleware(
    app: FastAPI,
    original_middleware_cls: type,
    replacement_middleware_cls: type,
    **replacement_kwargs,
) -> None:
    """
    Replace middleware (call from the plugin setup hook)

    :param app: FastAPI application instance
    :param original_middleware_cls: Original middleware class
    :param replacement_middleware_cls: Replacement middleware class
    :param replacement_kwargs: Initialization arguments for the replacement middleware
    :return:
    """
    for index, middleware in enumerate(app.user_middleware):
        if middleware.cls is original_middleware_cls:
            app.user_middleware[index] = Middleware(replacement_middleware_cls, **replacement_kwargs)
            return

    raise ValueError(f'{original_middleware_cls.__name__} not found in app.user_middleware')
