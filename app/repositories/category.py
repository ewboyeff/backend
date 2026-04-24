from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.category import Category
from app.models.region import Region


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all_active(self) -> list[Category]:
        result = await self.db.execute(
            select(Category)
            .options(noload(Category.funds))
            .where(Category.is_active == True)  # noqa: E712
            .order_by(Category.name_uz)
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[Category]:
        result = await self.db.execute(
            select(Category)
            .options(noload(Category.funds))
            .order_by(Category.name_uz)
        )
        return list(result.scalars().all())

    async def get_by_id(self, category_id: UUID) -> Category | None:
        result = await self.db.execute(
            select(Category)
            .options(noload(Category.funds))
            .where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.db.execute(
            select(Category)
            .options(noload(Category.funds))
            .where(Category.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Category:
        category = Category(**data)
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, category: Category, update_dict: dict) -> Category:
        for key, value in update_dict.items():
            setattr(category, key, value)
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self.db.delete(category)
        await self.db.flush()


class RegionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> list[Region]:
        result = await self.db.execute(
            select(Region)
            .options(noload(Region.funds), noload(Region.projects))
            .order_by(Region.name_uz)
        )
        return list(result.scalars().all())
