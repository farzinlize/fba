from fastapi import APIRouter

from backend.app.admin.api.v1.sys.data_rule import router as data_rule_router
from backend.app.admin.api.v1.sys.data_scope import router as data_scope_router
from backend.app.admin.api.v1.sys.dept import router as dept_router
from backend.app.admin.api.v1.sys.file import router as file_router
from backend.app.admin.api.v1.sys.menu import router as menu_router
from backend.app.admin.api.v1.sys.plugin import router as plugin_router
from backend.app.admin.api.v1.sys.role import router as role_router
from backend.app.admin.api.v1.sys.user import router as user_router

router = APIRouter(prefix='/sys')

router.include_router(dept_router, prefix='/depts', tags=['System departments'])
router.include_router(menu_router, prefix='/menus', tags=['System menus'])
router.include_router(role_router, prefix='/roles', tags=['System roles'])
router.include_router(user_router, prefix='/users', tags=['System users'])
router.include_router(data_rule_router, prefix='/data-rules', tags=['System data rules'])
router.include_router(data_scope_router, prefix='/data-scopes', tags=['System data scopes'])
router.include_router(file_router, prefix='/files', tags=['System files'])
router.include_router(plugin_router, prefix='/plugins', tags=['System plugins'])
