from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NewsCreate(BaseModel):
    fund_id: UUID | None = None
    title_uz: str = Field(min_length=2, max_length=255)
    title_ru: str | None = Field(default=None, max_length=255)
    title_en: str | None = Field(default=None, max_length=255)
    content_uz: str | None = None
    content_ru: str | None = None
    content_en: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=500)
    gradient: str | None = Field(default=None, max_length=100)
    read_time: int = Field(default=3, ge=1)
    is_featured: bool = False
    is_active: bool = True
    published_at: datetime | None = None


class NewsUpdate(BaseModel):
    fund_id: UUID | None = None
    title_uz: str | None = Field(default=None, min_length=2, max_length=255)
    title_ru: str | None = Field(default=None, max_length=255)
    title_en: str | None = Field(default=None, max_length=255)
    content_uz: str | None = None
    content_ru: str | None = None
    content_en: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=500)
    gradient: str | None = Field(default=None, max_length=100)
    read_time: int | None = Field(default=None, ge=1)
    is_featured: bool | None = None
    is_active: bool | None = None
    published_at: datetime | None = None


class NewsResponse(BaseModel):
    id: UUID
    fund_id: UUID | None
    title_uz: str
    title_ru: str | None
    title_en: str | None
    content_uz: str | None
    content_ru: str | None
    content_en: str | None
    image_url: str | None
    source_url: str | None
    gradient: str | None
    read_time: int
    is_featured: bool
    is_active: bool
    published_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
