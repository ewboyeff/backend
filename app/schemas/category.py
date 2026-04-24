from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name_uz: str = Field(min_length=2, max_length=255)
    name_ru: str | None = Field(default=None, max_length=255)
    name_en: str | None = Field(default=None, max_length=255)
    slug: str = Field(min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    icon_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name_uz: str | None = Field(default=None, min_length=2, max_length=255)
    name_ru: str | None = Field(default=None, max_length=255)
    name_en: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=255, pattern=r"^[a-z0-9-]+$")
    icon_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    id: UUID
    name_uz: str
    name_ru: str | None
    name_en: str | None
    slug: str
    icon_url: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RegionResponse(BaseModel):
    id: UUID
    name_uz: str
    name_ru: str | None
    name_en: str | None
    code: str

    model_config = ConfigDict(from_attributes=True)
