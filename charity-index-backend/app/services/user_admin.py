from __future__ import annotations

import math
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.base import PaginationMeta
from app.schemas.user import UserAdminUpdate


def _make_meta(page: int, per_page: int, total: int) -> PaginationMeta:
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginationMeta(page=page, per_page=per_page, total=total, total_pages=total_pages)


class UserAdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)

    async def get_list(
        self,
        page: int = 1,
        per_page: int = 20,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], PaginationMeta]:
        skip = (page - 1) * per_page
        users, total = await self.repo.get_list(
            role=role,
            is_active=is_active,
            skip=skip,
            limit=per_page,
        )
        return users, _make_meta(page, per_page, total)

    async def get_by_id(self, user_id: UUID) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "USER_NOT_FOUND", "message": "Foydalanuvchi topilmadi"},
            )
        return user

    async def update(self, user_id: UUID, data: UserAdminUpdate) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "USER_NOT_FOUND", "message": "Foydalanuvchi topilmadi"},
            )
        update_dict = data.model_dump(exclude_unset=True)
        return await self.repo.admin_update(user, update_dict)

    async def delete(self, user_id: UUID, current_user_id: UUID) -> None:
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "CANNOT_DELETE_SELF",
                    "message": "O'zingizni o'chira olmaysiz",
                },
            )
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "USER_NOT_FOUND", "message": "Foydalanuvchi topilmadi"},
            )
        await self.repo.delete(user_id)
