from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.user,
    ) -> User:
        return await self.create(
            {
                "email": email,
                "password_hash": hash_password(password),
                "full_name": full_name,
                "role": role,
            }
        )

    async def update_last_login(self, user_id: UUID) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.now(timezone.utc))
        )

    # ------------------------------------------------------------------
    # Admin operations
    # ------------------------------------------------------------------

    async def get_list(
        self,
        role: UserRole | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        stmt = select(User)
        count_stmt = select(func.count(User.id))

        conditions = []
        if role is not None:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active == is_active)

        if conditions:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def admin_update(self, user: User, update_dict: dict) -> User:
        for key, value in update_dict.items():
            setattr(user, key, value)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
