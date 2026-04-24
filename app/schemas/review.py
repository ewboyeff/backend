from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5, description="Ball (1–5)")
    comment: str | None = Field(default=None, max_length=2000)


class ReviewResponse(BaseModel):
    id: UUID
    fund_id: UUID
    user_id: UUID
    user_full_name: str | None = None
    rating: int
    comment: str | None
    is_approved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_user(cls, review: object) -> "ReviewResponse":
        user = getattr(review, "user", None)
        return cls(
            id=review.id,            # type: ignore[attr-defined]
            fund_id=review.fund_id,  # type: ignore[attr-defined]
            user_id=review.user_id,  # type: ignore[attr-defined]
            user_full_name=getattr(user, "full_name", None) if user else None,
            rating=review.rating,    # type: ignore[attr-defined]
            comment=review.comment,  # type: ignore[attr-defined]
            is_approved=review.is_approved,  # type: ignore[attr-defined]
            created_at=review.created_at,    # type: ignore[attr-defined]
        )
