from fastapi import APIRouter

from backend.core.conf import settings
from backend.plugin.email.api.v1.email import router as email_router

v1 = APIRouter(prefix=f'{settings.FASTAPI_API_V1_PATH}/emails', tags=['Email'])

v1.include_router(email_router)
