from __future__ import annotations

import math
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.repositories.review import ReviewRepository
from app.schemas.base import PaginationMeta
from app.schemas.review import ReviewCreate


def _make_meta(page: int, per_page: int, total: int) -> PaginationMeta:
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginationMeta(page=page, per_page=per_page, total=total, total_pages=total_pages)


class ReviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ReviewRepository(db)

    async def create(
        self, fund_id: UUID, user_id: UUID, data: ReviewCreate
    ) -> Review:
        existing = await self.repo.get_by_fund_and_user(fund_id, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "REVIEW_ALREADY_EXISTS",
                    "message": "Siz bu fond uchun allaqachon sharh yozgansiz",
                },
            )
        return await self.repo.create(
            fund_id=fund_id,
            user_id=user_id,
            rating=data.rating,
            comment=data.comment,
        )

    async def get_by_fund(
        self,
        fund_id: UUID,
        page: int = 1,
        per_page: int = 20,
        only_approved: bool = True,
    ) -> tuple[list[Review], PaginationMeta]:
        skip = (page - 1) * per_page
        reviews, total = await self.repo.get_by_fund(
            fund_id=fund_id,
            only_approved=only_approved,
            skip=skip,
            limit=per_page,
        )
        return reviews, _make_meta(page, per_page, total)

    async def get_all(
        self,
        only_approved: bool | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> tuple[list[Review], PaginationMeta]:
        skip = (page - 1) * per_page
        reviews, total = await self.repo.get_all(
            only_approved=only_approved, skip=skip, limit=per_page
        )
        return reviews, _make_meta(page, per_page, total)

    async def approve(self, review_id: UUID) -> Review:
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "REVIEW_NOT_FOUND", "message": "Sharh topilmadi"},
            )
        return await self.repo.approve(review)

    async def delete(self, review_id: UUID) -> None:
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "REVIEW_NOT_FOUND", "message": "Sharh topilmadi"},
            )
        await self.repo.delete(review)
