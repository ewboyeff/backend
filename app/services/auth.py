from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserLogin, UserRegister


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.user_repo = UserRepository(db)

    async def register(
        self, data: UserRegister
    ) -> tuple[User, str, str]:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_ALREADY_EXISTS",
                    "message": "Bu email allaqachon ro'yxatdan o'tgan",
                },
            )

        user = await self.user_repo.create_user(
            email=data.email,
            password=data.password,
            full_name=data.full_name,
        )

        token_data = {"sub": str(user.id), "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return user, access_token, refresh_token

    async def login(
        self, data: UserLogin
    ) -> tuple[User, str, str]:
        user = await self.user_repo.get_by_email(data.email)

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Email yoki parol noto'g'ri",
                },
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "USER_INACTIVE",
                    "message": "Hisobingiz bloklangan",
                },
            )

        await self.user_repo.update_last_login(user.id)

        token_data = {"sub": str(user.id), "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return user, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> str:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_TOKEN",
                    "message": "Token turi noto'g'ri",
                },
            )

        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Token noto'g'ri"},
            )

        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "USER_NOT_FOUND",
                    "message": "Foydalanuvchi topilmadi",
                },
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "USER_INACTIVE",
                    "message": "Hisobingiz bloklangan",
                },
            )

        return create_access_token({"sub": str(user.id), "role": user.role})
