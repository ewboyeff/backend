from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PartnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    logo_url: str | None = Field(default=None, max_length=500)
    website_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True
    order_index: int = 0


class PartnerUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    logo_url: str | None = None
    website_url: str | None = None
    is_active: bool | None = None
    order_index: int | None = None


class PartnerResponse(BaseModel):
    id: UUID
    name: str
    logo_url: str | None
    website_url: str | None
    is_active: bool
    order_index: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
