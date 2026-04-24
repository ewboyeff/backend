from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.region import Region
from app.repositories.category import CategoryRepository, RegionRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = CategoryRepository(db)

    async def get_all(self, only_active: bool = True) -> list[Category]:
        if only_active:
            return await self.repo.get_all_active()
        return await self.repo.get_all()

    async def get_by_id(self, category_id: UUID) -> Category:
        cat = await self.repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CATEGORY_NOT_FOUND", "message": "Kategoriya topilmadi"},
            )
        return cat

    async def create(self, data: CategoryCreate) -> Category:
        existing = await self.repo.get_by_slug(data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "SLUG_ALREADY_EXISTS",
                    "message": f"'{data.slug}' slug allaqachon mavjud",
                },
            )
        return await self.repo.create(data.model_dump())

    async def update(self, category_id: UUID, data: CategoryUpdate) -> Category:
        cat = await self.repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CATEGORY_NOT_FOUND", "message": "Kategoriya topilmadi"},
            )
        update_dict = data.model_dump(exclude_unset=True)
        if "slug" in update_dict and update_dict["slug"] != cat.slug:
            existing = await self.repo.get_by_slug(update_dict["slug"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "SLUG_ALREADY_EXISTS",
                        "message": f"'{update_dict['slug']}' slug allaqachon mavjud",
                    },
                )
        return await self.repo.update(cat, update_dict)

    async def delete(self, category_id: UUID) -> None:
        cat = await self.repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CATEGORY_NOT_FOUND", "message": "Kategoriya topilmadi"},
            )
        await self.repo.delete(cat)


class RegionService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = RegionRepository(db)

    async def get_all(self) -> list[Region]:
        return await self.repo.get_all()
