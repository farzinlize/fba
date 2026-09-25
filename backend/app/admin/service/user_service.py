from collections.abc import Sequence
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_dept import dept_dao
from backend.app.admin.crud.crud_role import role_dao
from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model import Role, User
from backend.app.admin.schema.user import (
    AddUserParam,
    ResetPasswordParam,
    UpdateUserParam,
)
from backend.app.admin.schema.user_password_history import CreateUserPasswordHistoryParam
from backend.app.admin.service.user_password_history_service import password_security_service
from backend.app.admin.utils.password_security import password_verify, validate_new_password
from backend.common.context import ctx
from backend.common.enums import UserPermissionType
from backend.common.exception import errors
from backend.common.pagination import paging_data
from backend.common.response.response_code import CustomErrorCode
from backend.common.security.jwt import jwt_decode
from backend.common.security.token import get_token, revoke_user_tokens
from backend.core.conf import settings
from backend.database.redis import redis_client
from backend.utils.serializers import select_join_serialize


class UserService:
    """User service"""

    @staticmethod
    async def get_userinfo(*, db: AsyncSession, pk: int | None = None, username: str | None = None) -> User:
        """
        Get user information

        :param db: Database session
        :param pk: User ID
        :param username: Username
        :return:
        """
        user = await user_dao.get_join(db, user_id=pk, username=username)
        if not user:
            raise errors.NotFoundError(msg='User does not exist')
        return user

    @staticmethod
    async def get_roles(*, db: AsyncSession, pk: int) -> Sequence[Role]:
        """
        Get all user roles

        :param db: Database session
        :param pk: User ID
        :return:
        """
        user = await user_dao.get_join(db, user_id=pk)
        if not user:
            raise errors.NotFoundError(msg='User does not exist')
        return user.roles

    @staticmethod
    async def get_list(*, db: AsyncSession, dept: int, username: str, phone: str, status: int) -> dict[str, Any]:
        """
        Get user list

        :param db: Database session
        :param dept: Department ID
        :param username: Username
        :param phone: Mobile number
        :param status: Status
        :return:
        """
        user_select = await user_dao.get_select(dept=dept, username=username, phone=phone, status=status)
        data = await paging_data(db, user_select)
        if data['items']:
            serialized_items = select_join_serialize(data['items'], relationships=['User-m2o-Dept', 'User-m2m-Role'])
            # Ensure the result is a list, even when it contains only one item
            data['items'] = [serialized_items] if not isinstance(serialized_items, list) else serialized_items
        return data

    @staticmethod
    async def create(*, db: AsyncSession, obj: AddUserParam) -> None:
        """
        Create user

        :param db: Database session
        :param obj: User creation parameters
        :return:
        """
        if await user_dao.get_by_username(db, obj.username):
            raise errors.ConflictError(msg='Username is already registered')
        if obj.email and await user_dao.check_email(db, obj.email):
            raise errors.ConflictError(msg='Email is already associated with an account')
        if not obj.password:
            raise errors.RequestError(msg='Password must not be empty')
        if not await dept_dao.get(db, obj.dept_id):
            raise errors.NotFoundError(msg='Department does not exist')
        if obj.roles:
            roles = await role_dao.get_all_by_ids(db, list(set(obj.roles)))
            if {role.id for role in roles} != set(obj.roles):
                raise errors.NotFoundError(msg='Role does not exist')
        obj.nickname = obj.nickname or obj.username
        await user_dao.add(db, obj)

    @staticmethod
    async def update(*, db: AsyncSession, pk: int, obj: UpdateUserParam) -> int:
        """
        Update user information

        :param db: Database session
        :param pk: User ID
        :param obj: User update parameters
        :return:
        """
        user = await user_dao.get_join(db, user_id=pk)
        if not user:
            raise errors.NotFoundError(msg='User does not exist')
        if obj.username != user.username and await user_dao.get_by_username(db, obj.username):
            raise errors.ConflictError(msg='Username is already registered')
        if obj.email and obj.email != user.email:
            email_user = await user_dao.check_email(db, obj.email)
            if email_user:
                raise errors.ConflictError(msg='Email is already associated with an account')
        if obj.dept_id and obj.dept_id != user.dept_id and not await dept_dao.get(db, dept_id=obj.dept_id):
            raise errors.NotFoundError(msg='Department does not exist')
        if obj.roles:
            roles = await role_dao.get_all_by_ids(db, list(set(obj.roles)))
            if {role.id for role in roles} != set(obj.roles):
                raise errors.NotFoundError(msg='Role does not exist')
        count = await user_dao.update(db, user.id, obj)
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user.id}')
        return count

    @staticmethod
    async def update_permission(*, db: AsyncSession, request: Request, pk: int, type: UserPermissionType) -> int:  # ruff:ignore[complex-structure]
        """
        Update user permissions

        :param db: Database session
        :param request: FastAPI request object
        :param pk: User ID
        :param type: Permission type
        :return:
        """
        match type:
            case UserPermissionType.superuser:
                user = await user_dao.get(db, pk)
                if not user:
                    raise errors.NotFoundError(msg='User does not exist')
                if pk == request.user.id:
                    raise errors.ForbiddenError(msg='Cannot modify your own permissions')
                count = await user_dao.set_super(db, pk, is_super=not user.is_superuser)
            case UserPermissionType.staff:
                user = await user_dao.get(db, pk)
                if not user:
                    raise errors.NotFoundError(msg='User does not exist')
                if pk == request.user.id:
                    raise errors.ForbiddenError(msg='Cannot modify your own permissions')
                count = await user_dao.set_staff(db, pk, is_staff=not user.is_staff)
            case UserPermissionType.status:
                user = await user_dao.get(db, pk)
                if not user:
                    raise errors.NotFoundError(msg='User does not exist')
                if pk == request.user.id:
                    raise errors.ForbiddenError(msg='Cannot modify your own permissions')
                count = await user_dao.set_status(db, pk, 0 if user.status == 1 else 1)
            case UserPermissionType.multi_login:
                user = await user_dao.get(db, pk)
                if not user:
                    raise errors.NotFoundError(msg='User does not exist')
                multi_login = user.is_multi_login if pk != request.user.id else request.user.is_multi_login
                new_multi_login = not multi_login
                count = await user_dao.set_multi_login(db, pk, multi_login=new_multi_login)
                token = get_token(request)
                token_payload = jwt_decode(token)
                if pk == request.user.id:
                    # When administrators update themselves, invalidate all tokens except the current one
                    if not new_multi_login:
                        await revoke_user_tokens(user.id, exclude_session_uuid=token_payload.session_uuid)
                else:
                    # When administrators update other users, invalidate all tokens of those users
                    if not new_multi_login:
                        await revoke_user_tokens(user.id)
            case _:
                raise errors.RequestError(msg='Permission type does not exist')

        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user.id}')
        return count

    @staticmethod
    async def reset_password(*, db: AsyncSession, pk: int, password: str) -> int:
        """
        Reset user password

        :param db: Database session
        :param pk: User ID
        :param password: New password
        :return:
        """
        user = await user_dao.get(db, pk)
        if not user:
            raise errors.NotFoundError(msg='User does not exist')

        await validate_new_password(db, user.id, password)
        count = await user_dao.reset_password(db, user.id, password)
        history_obj = CreateUserPasswordHistoryParam(user_id=user.id, password=user.password)
        await password_security_service.save_password_history(db, history_obj)
        await user_dao.update_password_changed_time(db, user.id)
        await revoke_user_tokens(user.id)
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user.id}')

        return count

    @staticmethod
    async def update_nickname(*, db: AsyncSession, user_id: int, nickname: str) -> int:
        """
        Update current user nickname

        :param db: Database session
        :param user_id: User ID
        :param nickname: User nickname
        :return:
        """
        count = await user_dao.update_nickname(db, user_id, nickname)
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}')
        return count

    @staticmethod
    async def update_avatar(*, db: AsyncSession, user_id: int, avatar: str) -> int:
        """
        Update current user avatar

        :param db: Database session
        :param user_id: User ID
        :param avatar: Avatar URL
        :return:
        """
        count = await user_dao.update_avatar(db, user_id, avatar)
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}')
        return count

    @staticmethod
    async def update_email(*, db: AsyncSession, user_id: int, captcha: str, email: str) -> int:
        """
        Update current user email

        :param db: Database session
        :param user_id: User ID
        :param captcha: Email verification code
        :param email: Email
        :return:
        """
        captcha_key = f'{settings.EMAIL_CAPTCHA_REDIS_PREFIX}:{ctx.ip}'
        captcha_code = await redis_client.get(captcha_key)
        if not captcha_code:
            raise errors.RequestError(msg='Verification code has expired; request a new one')
        if captcha != captcha_code:
            raise errors.CustomError(error=CustomErrorCode.CAPTCHA_ERROR)
        email_user = await user_dao.check_email(db, email)
        if email_user and email_user.id != user_id:
            raise errors.ConflictError(msg='Email is already associated with an account')
        await redis_client.delete(captcha_key)
        count = await user_dao.update_email(db, user_id, email)
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}')
        return count

    @staticmethod
    async def update_password(*, db: AsyncSession, user_id: int, obj: ResetPasswordParam) -> int:
        """
        Update current user password

        :param db: Database session
        :param user_id: User ID
        :param obj: Password reset parameters
        :return:
        """
        user = await user_dao.get(db, user_id)
        if user.password and not password_verify(obj.old_password, user.password):
            raise errors.RequestError(msg='Incorrect current password')
        if obj.new_password != obj.confirm_password:
            raise errors.RequestError(msg='The two passwords do not match')

        await validate_new_password(db, user_id, obj.new_password)
        count = await user_dao.reset_password(db, user_id, obj.new_password)
        history_obj = CreateUserPasswordHistoryParam(user_id=user.id, password=user.password)
        await password_security_service.save_password_history(db, history_obj)
        await user_dao.update_password_changed_time(db, user.id)
        await revoke_user_tokens(user_id)
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user_id}')

        return count

    @staticmethod
    async def delete(*, db: AsyncSession, pk: int) -> int:
        """
        Delete user

        :param db: Database session
        :param pk: User ID
        :return:
        """
        user = await user_dao.get(db, pk)
        if not user:
            raise errors.NotFoundError(msg='User does not exist')

        count = await user_dao.delete(db, user.id)
        await revoke_user_tokens(user.id)
        await redis_client.delete(f'{settings.JWT_USER_REDIS_PREFIX}:{user.id}')

        return count


user_service: UserService = UserService()
