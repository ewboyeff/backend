from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.complaint import ComplaintStatus


class ComplaintCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=5000)


class ComplaintUpdate(BaseModel):
    status: ComplaintStatus | None = None
    admin_note: str | None = Field(default=None, max_length=2000)


class ComplaintResponse(BaseModel):
    id: UUID
    fund_id: UUID
    user_id: UUID
    user_full_name: str | None = None
    reason: str
    description: str | None
    status: ComplaintStatus
    admin_note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_user(cls, complaint) -> "ComplaintResponse":
        user = getattr(complaint, "user", None)
        return cls(
            id=complaint.id,
            fund_id=complaint.fund_id,
            user_id=complaint.user_id,
            user_full_name=getattr(user, "full_name", None),
            reason=complaint.reason,
            description=complaint.description,
            status=complaint.status,
            admin_note=complaint.admin_note,
            created_at=complaint.created_at,
        )
