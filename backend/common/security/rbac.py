from fastapi import Depends, Request

from backend.common.context import ctx
from backend.common.enums import MethodType, StatusType
from backend.common.exception import errors
from backend.common.security.jwt import DependsJwtAuth
from backend.core.conf import settings


async def rbac_verify(request: Request, _token: str = DependsJwtAuth) -> None:  # ruff:ignore[complex-structure]
    """
    RBAC permission checks (authorization order matters; modify carefully)

    :param request: FastAPI request object
    :param _token: JWT token
    :return:
    """
    path = request.url.path

    # API authorization allowlist
    if path in settings.TOKEN_REQUEST_PATH_EXCLUDE:
        return
    for pattern in settings.TOKEN_REQUEST_PATH_EXCLUDE_PATTERN:
        if pattern.match(path):
            return

    # Enforce JWT authentication status validation
    if not request.auth.scopes:
        raise errors.TokenError

    # Skip validation for superusers
    if request.user.is_superuser:
        return

    # Check user roles
    user_roles = request.user.roles
    enabled_roles = [role for role in user_roles if role.status == StatusType.enable]
    if not enabled_roles:
        raise errors.AuthorizationError(msg='User role is locked; contact the system administrator')

    # Check menus assigned to user roles
    if not any(len(role.menus) > 0 for role in enabled_roles):
        raise errors.AuthorizationError(msg='No menus assigned to the user; contact the system administrator')

    # Check admin panel operation permissions
    method = request.method
    if method not in {MethodType.GET, MethodType.OPTIONS} and not request.user.is_staff:
        raise errors.AuthorizationError(
            msg='User is prohibited from admin panel operations; contact the system administrator'
        )

    # RBAC authorization
    if settings.RBAC_ROLE_MENU_MODE:
        path_auth_perm = ctx.permission

        # Skip validation when no menu operation permission identifier is set
        if not path_auth_perm:
            return

        # Menu authorization allowlist
        if path_auth_perm in settings.RBAC_ROLE_MENU_EXCLUDE:
            return

        # Deduplicate menus
        unique_menus = {}
        for role in enabled_roles:
            for menu in role.menus:
                unique_menus[menu.id] = menu

        # Validate assigned menu permissions
        allow_perms = []
        for menu in list(unique_menus.values()):
            if menu.perms and menu.status == StatusType.enable:
                allow_perms.extend(menu.perms.split(','))
        if path_auth_perm not in allow_perms:
            raise errors.AuthorizationError
    else:
        # Casbin mode
        try:
            from backend.plugin.casbin_rbac.rbac import casbin_verify
        except ImportError:
            raise errors.ServerError(
                msg='Failed to import Casbin RBAC plugin utilities; contact the system administrator'
            )

        await casbin_verify(request)


# RBAC authorization dependency injection
DependsRBAC = Depends(rbac_verify)
