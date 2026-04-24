from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApplicationCreate(BaseModel):
    type: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=255)
    organization: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    message: str | None = Field(default=None, max_length=5000)


class ApplicationResponse(BaseModel):
    id: UUID
    type: str
    full_name: str
    organization: str | None
    phone: str | None
    email: str | None
    message: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
