from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.fund import Fund
    from app.models.user import User


class ComplaintStatus(str, Enum):
    pending = "pending"
    reviewed = "reviewed"
    resolved = "resolved"


class Complaint(Base):
    __tablename__ = "complaints"

    fund_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("funds.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ComplaintStatus] = mapped_column(
        SQLEnum(ComplaintStatus, name="complaint_status"),
        default=ComplaintStatus.pending,
        nullable=False,
    )
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    fund: Mapped[Fund] = relationship(
        back_populates="complaints",
        lazy="selectin",
    )
    user: Mapped[User] = relationship(
        back_populates="complaints",
        lazy="selectin",
    )

