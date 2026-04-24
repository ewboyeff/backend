from __future__ import annotations

from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> ModelType | None:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[ModelType]:
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: UUID) -> bool:
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return False
        await self.db.delete(db_obj)
        await self.db.flush()
        return True

    async def count(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()
