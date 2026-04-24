from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Parol kamida 8 ta belgidan iborat bo'lishi kerak")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError(
                "Ism-familiya kamida 2 ta belgidan iborat bo'lishi kerak"
            )
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# Admin user management schemas
# ---------------------------------------------------------------------------


class UserAdminUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    fund_id: UUID | None = None
    preferred_language: str | None = None


class UserDetailResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    fund_id: UUID | None
    preferred_language: str
    last_login: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
