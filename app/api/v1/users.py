from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.base import DataResponse, PaginatedResponse
from app.schemas.user import UserAdminUpdate, UserDetailResponse
from app.services.user_admin import UserAdminService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserDetailResponse])
async def list_users(
    role: UserRole | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Foydalanuvchilar ro'yxati (faqat admin).
    """
    service = UserAdminService(db)
    users, meta = await service.get_list(
        page=page, per_page=per_page, role=role, is_active=is_active
    )
    return PaginatedResponse(
        data=[UserDetailResponse.model_validate(u) for u in users],
        meta=meta,
    )


@router.get("/{user_id}", response_model=DataResponse[UserDetailResponse])
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Foydalanuvchi ma'lumotlari (faqat admin).
    """
    service = UserAdminService(db)
    user = await service.get_by_id(user_id)
    return DataResponse(data=UserDetailResponse.model_validate(user))


@router.put("/{user_id}", response_model=DataResponse[UserDetailResponse])
async def update_user(
    user_id: UUID,
    data: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Foydalanuvchini yangilash (faqat admin): rol, holat, fond bog'lash.
    """
    service = UserAdminService(db)
    user = await service.update(user_id, data)
    return DataResponse(
        message="Foydalanuvchi muvaffaqiyatli yangilandi",
        data=UserDetailResponse.model_validate(user),
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Foydalanuvchini o'chirish (faqat admin). Admin o'zini o'chira olmaydi.
    """
    service = UserAdminService(db)
    await service.delete(user_id, current_user_id=current_user.id)
