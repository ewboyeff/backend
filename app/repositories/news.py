from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News


class NewsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, news_id: UUID) -> News | None:
        result = await self.db.execute(
            select(News).where(News.id == news_id)
        )
        return result.scalar_one_or_none()

    async def get_list(
        self,
        only_active: bool = True,
        is_featured: bool | None = None,
        fund_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[News], int]:
        stmt = select(News)
        count_stmt = select(func.count(News.id))

        conditions = []
        if only_active:
            conditions.append(News.is_active == True)  # noqa: E712
        if is_featured is not None:
            conditions.append(News.is_featured == is_featured)
        if fund_id is not None:
            conditions.append(News.fund_id == fund_id)

        if conditions:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        stmt = stmt.order_by(News.published_at.desc().nullslast(), News.created_at.desc()).offset(skip).limit(limit)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def create(self, data: dict) -> News:
        news = News(**data)
        self.db.add(news)
        await self.db.flush()
        await self.db.refresh(news)
        return news

    async def update(self, news: News, update_dict: dict) -> News:
        for key, value in update_dict.items():
            setattr(news, key, value)
        self.db.add(news)
        await self.db.flush()
        await self.db.refresh(news)
        return news

    async def delete(self, news: News) -> None:
        await self.db.delete(news)
        await self.db.flush()
