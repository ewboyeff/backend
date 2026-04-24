from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, review_id: UUID) -> Review | None:
        result = await self.db.execute(
            select(Review).where(Review.id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_by_fund_and_user(
        self, fund_id: UUID, user_id: UUID
    ) -> Review | None:
        result = await self.db.execute(
            select(Review).where(
                Review.fund_id == fund_id,
                Review.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_fund(
        self,
        fund_id: UUID,
        only_approved: bool = True,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Review], int]:
        from sqlalchemy import func

        stmt = select(Review).where(Review.fund_id == fund_id)
        count_stmt = select(func.count(Review.id)).where(Review.fund_id == fund_id)

        if only_approved:
            stmt = stmt.where(Review.is_approved == True)  # noqa: E712
            count_stmt = count_stmt.where(Review.is_approved == True)  # noqa: E712

        stmt = stmt.order_by(Review.created_at.desc()).offset(skip).limit(limit)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, fund_id: UUID, user_id: UUID, rating: int, comment: str | None) -> Review:
        review = Review(
            fund_id=fund_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            is_approved=False,
        )
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def get_all(
        self,
        only_approved: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Review], int]:
        from sqlalchemy import func

        stmt = select(Review)
        count_stmt = select(func.count(Review.id))

        if only_approved is True:
            stmt = stmt.where(Review.is_approved == True)   # noqa: E712
            count_stmt = count_stmt.where(Review.is_approved == True)  # noqa: E712
        elif only_approved is False:
            stmt = stmt.where(Review.is_approved == False)  # noqa: E712
            count_stmt = count_stmt.where(Review.is_approved == False)  # noqa: E712

        stmt = stmt.order_by(Review.created_at.desc()).offset(skip).limit(limit)

        total = (await self.db.execute(count_stmt)).scalar_one()
        rows = list((await self.db.execute(stmt)).scalars().all())
        return rows, total

    async def approve(self, review: Review) -> Review:
        review.is_approved = True
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def delete(self, review: Review) -> None:
        await self.db.delete(review)
        await self.db.flush()
