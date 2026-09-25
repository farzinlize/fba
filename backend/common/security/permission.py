from typing import TYPE_CHECKING, Any

from fastapi import Request
from sqlalchemy import Alias, ColumnElement, Table, and_, or_
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy_crud_plus.types import Model

from backend.common.context import ctx
from backend.common.enums import RoleDataRuleExpressionType, RoleDataRuleOperatorType
from backend.common.exception import errors
from backend.core.conf import settings
from backend.utils.dynamic_import import get_all_models
from backend.utils.timezone import timezone

if TYPE_CHECKING:
    from backend.app.admin.model import DataRule


class RequestPermission:
    """
    Request permission validator for role-menu RBAC

    Note:
        Place `Depends(RequestPermission('xxx'))` before `DependsRBAC` when using this permission check,
        because the current FastAPI version resolves endpoint dependencies in order,
        setting the RBAC identifier before validation
    """

    def __init__(self, value: str) -> None:
        """
        Initialize request permission validator

        :param value: Permission identifier
        :return:
        """
        self.value = value

    async def __call__(self, request: Request) -> None:
        """
        Validate request permissions

        :param request: FastAPI request object
        :return:
        """
        if settings.RBAC_ROLE_MENU_MODE:
            if not isinstance(self.value, str):
                raise errors.ServerError

            # Set permission identifier in context
            ctx.permission = self.value


def get_data_permission_models() -> dict[str, object]:
    """Get all models available for data permissions"""
    return {getattr(model, '__name__', str(model)): model for model in get_all_models()}


def filter_data_permission(  # ruff:ignore[complex-structure]
    request: Request, *models: type[Model] | AliasedClass | Alias | Table
) -> ColumnElement[bool]:
    """
    Filter data permissions to control which data users can access

    Use cases:
        - Control which data users can see

    :param request: FastAPI request object
    :param models: Model class to which data permissions apply
    :return:
    """
    # Do not filter superusers
    if request.user.is_superuser:
        return or_(1 == 1)

    # Data permission filtering is not enabled for the role
    for role in request.user.roles:
        if role.status and not role.is_filter_scopes:
            return or_(1 == 1)

    # Get data rules
    data_rules: set[DataRule] = set()
    for role in request.user.roles:
        if not role.status:
            continue
        for scope in role.scopes:
            if scope.status:
                data_rules.update(rule for rule in scope.rules if rule is not None)

    # Data permission filtering is enabled, but no enabled data permissions exist
    if not data_rules:
        return or_(1 != 1)

    # Target model
    target_model_map = (
        {getattr(model, '__name__', str(model)): model for model in models} if models else get_data_permission_models()
    )

    # Field template variable mapping
    column_template_resolvers = {
        var['key']: var['key'].strip('_') for var in settings.DATA_PERMISSION_COLUMN_TEMPLATE_VARIABLES
    }

    # Template variable resolution mapping
    template_variable_keys = {var['key'] for var in settings.DATA_PERMISSION_TEMPLATE_VARIABLES}
    template_resolvers = {
        '${user_id}': request.user.id,
        '${dept_id}': request.user.dept_id,
        '${now}': timezone.now,
    }

    where_and_list = []
    where_or_list = []

    for data_rule in data_rules:
        if data_rule.model == '__ALL__':
            target_models = list(target_model_map.values())
        else:
            target_model = target_model_map.get(data_rule.model)
            target_models = [target_model] if target_model is not None else []

        for target_model in target_models:
            table = target_model if isinstance(target_model, Table) else target_model.__table__
            rule_column = column_template_resolvers.get(data_rule.column, data_rule.column)
            if rule_column not in table.columns.keys():
                continue
            if rule_column in settings.DATA_PERMISSION_COLUMN_EXCLUDE:
                continue

            # Build filter conditions
            column_obj = (
                getattr(target_model, rule_column)
                if not isinstance(target_model, Table)
                else table.columns[rule_column]
            )
            column_type = table.columns[rule_column].type.python_type

            def cast_value(value: Any, _column_type: type = column_type) -> Any:
                """Type conversion"""
                try:
                    if value in template_variable_keys:
                        return _column_type(template_resolvers[value])
                    return _column_type(value) if _column_type is not str else value
                except (ValueError, TypeError):
                    return value

            condition = None
            match data_rule.expression:
                case RoleDataRuleExpressionType.eq:
                    condition = column_obj == cast_value(data_rule.value)
                case RoleDataRuleExpressionType.ne:
                    condition = column_obj != cast_value(data_rule.value)
                case RoleDataRuleExpressionType.gt:
                    condition = column_obj > cast_value(data_rule.value)
                case RoleDataRuleExpressionType.ge:
                    condition = column_obj >= cast_value(data_rule.value)
                case RoleDataRuleExpressionType.lt:
                    condition = column_obj < cast_value(data_rule.value)
                case RoleDataRuleExpressionType.le:
                    condition = column_obj <= cast_value(data_rule.value)
                case RoleDataRuleExpressionType.in_:
                    values = [cast_value(v.strip()) for v in data_rule.value.split(',')]
                    condition = column_obj.in_(values)
                case RoleDataRuleExpressionType.not_in:
                    values = [cast_value(v.strip()) for v in data_rule.value.split(',')]
                    condition = column_obj.not_in(values)

            # Add to the corresponding list based on the operator
            if condition is not None:
                match data_rule.operator:
                    case RoleDataRuleOperatorType.AND:
                        where_and_list.append(condition)
                    case RoleDataRuleOperatorType.OR:
                        where_or_list.append(condition)

    # Combine all conditions
    where_list = []
    if where_and_list:
        where_list.append(and_(*where_and_list))
    if where_or_list:
        where_list.append(or_(*where_or_list))

    return or_(*where_list) if where_list else or_(1 == 1)


# This function simplifies calls but does not currently work: https://github.com/fastapi/fastapi/discussions/14438
# def DataPermissionFilter(*models: type[Model] | AliasedClass | Alias | Table) -> type[ColumnElement[bool]]:
#     """
#     Data permission filter for the specified models
#
#     :param models: Model classes (optional; multiple supported)
#     :return:
#     """
#     return Annotated[ColumnElement[bool], Depends(partial(filter_data_permission, *models))]


class DataPermissionFilter:
    """Data permission filter for the specified models"""

    def __init__(self, *models: type[Model] | AliasedClass | Alias | Table) -> None:
        self.models = models

    async def __call__(self, request: Request) -> ColumnElement[bool]:
        return filter_data_permission(request, *self.models)
