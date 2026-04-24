from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.base import DataResponse, PaginatedResponse
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.review import ReviewService

router = APIRouter(prefix="/funds", tags=["Reviews"])


@router.post(
    "/{fund_id}/reviews",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[ReviewResponse],
)
async def create_review(
    fund_id: UUID,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fond uchun sharh yozish (autentifikatsiya talab qilinadi).
    Bir foydalanuvchi bir fondga faqat bitta sharh yoza oladi.
    """
    service = ReviewService(db)
    review = await service.create(fund_id=fund_id, user_id=current_user.id, data=data)
    return DataResponse(
        message="Sharh muvaffaqiyatli yuborildi",
        data=ReviewResponse.model_validate(review),
    )


@router.get(
    "/{fund_id}/reviews",
    response_model=PaginatedResponse[ReviewResponse],
)
async def get_reviews(
    fund_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Fond sharhlari ro'yxati (faqat tasdiqlangan).
    """
    service = ReviewService(db)
    reviews, meta = await service.get_by_fund(
        fund_id=fund_id, page=page, per_page=per_page, only_approved=True
    )
    return PaginatedResponse(
        data=[ReviewResponse.from_orm_with_user(r) for r in reviews],
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Moderator / Admin endpoints (separate prefix)
# ---------------------------------------------------------------------------

reviews_admin_router = APIRouter(prefix="/reviews", tags=["Reviews"])


@reviews_admin_router.get(
    "",
    response_model=PaginatedResponse[ReviewResponse],
)
async def list_reviews(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    is_approved: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.moderator, UserRole.admin)),
):
    service = ReviewService(db)
    reviews, meta = await service.get_all(only_approved=is_approved, page=page, per_page=per_page)
    return PaginatedResponse(
        data=[ReviewResponse.from_orm_with_user(r) for r in reviews],
        meta=meta,
    )


@reviews_admin_router.put(
    "/{review_id}/approve",
    response_model=DataResponse[ReviewResponse],
)
async def approve_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.moderator, UserRole.admin)),
):
    """
    Sharhni tasdiqlash (moderator yoki admin).
    """
    service = ReviewService(db)
    review = await service.approve(review_id)
    return DataResponse(
        message="Sharh tasdiqlandi",
        data=ReviewResponse.model_validate(review),
    )


@reviews_admin_router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Sharhni o'chirish (faqat admin).
    """
    service = ReviewService(db)
    await service.delete(review_id)
