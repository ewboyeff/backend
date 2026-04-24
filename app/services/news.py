from __future__ import annotations

import math
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News
from app.repositories.news import NewsRepository
from app.schemas.base import PaginationMeta
from app.schemas.news import NewsCreate, NewsUpdate


def _make_meta(page: int, per_page: int, total: int) -> PaginationMeta:
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginationMeta(page=page, per_page=per_page, total=total, total_pages=total_pages)


class NewsService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = NewsRepository(db)

    async def get_list(
        self,
        page: int = 1,
        per_page: int = 20,
        is_featured: bool | None = None,
        fund_id: UUID | None = None,
        only_active: bool = True,
    ) -> tuple[list[News], PaginationMeta]:
        skip = (page - 1) * per_page
        news_list, total = await self.repo.get_list(
            only_active=only_active,
            is_featured=is_featured,
            fund_id=fund_id,
            skip=skip,
            limit=per_page,
        )
        return news_list, _make_meta(page, per_page, total)

    async def get_by_id(self, news_id: UUID) -> News:
        news = await self.repo.get_by_id(news_id)
        if not news:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NEWS_NOT_FOUND", "message": "Yangilik topilmadi"},
            )
        return news

    async def create(self, data: NewsCreate) -> News:
        return await self.repo.create(data.model_dump())

    async def update(self, news_id: UUID, data: NewsUpdate) -> News:
        news = await self.repo.get_by_id(news_id)
        if not news:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NEWS_NOT_FOUND", "message": "Yangilik topilmadi"},
            )
        update_dict = data.model_dump(exclude_unset=True)
        return await self.repo.update(news, update_dict)

    async def delete(self, news_id: UUID) -> None:
        news = await self.repo.get_by_id(news_id)
        if not news:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NEWS_NOT_FOUND", "message": "Yangilik topilmadi"},
            )
        await self.repo.delete(news)
