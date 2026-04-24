from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.fund import Fund
    from app.models.region import Region


class ProjectStatus(str, Enum):
    planned = "planned"
    active = "active"
    completed = "completed"


class Project(Base):
    __tablename__ = "projects"

    fund_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("funds.id", ondelete="CASCADE"),
        nullable=False,
    )
    title_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus, name="project_status"),
        default=ProjectStatus.planned,
        nullable=False,
    )
    budget: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    spent: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="UZS", nullable=False)
    beneficiaries_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    region_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        nullable=True,
    )

    fund: Mapped[Fund] = relationship(
        back_populates="projects",
        lazy="selectin",
    )
    region: Mapped[Region | None] = relationship(
        back_populates="projects",
        lazy="selectin",
    )

