from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.complaint import Complaint
    from app.models.index import FundIndex, FundIndexScore
    from app.models.news import News
    from app.models.project import Project
    from app.models.region import Region
    from app.models.report import FinancialReport
    from app.models.review import Review
    from app.models.user import User


class FundStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class Fund(Base):
    __tablename__ = "funds"

    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_initials: Mapped[str | None] = mapped_column(String(10), nullable=True)
    logo_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    director_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    legal_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    inn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    region_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        nullable=True,
    )
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    telegram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    donation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[FundStatus] = mapped_column(
        SQLEnum(FundStatus, name="fund_status"),
        default=FundStatus.active,
        nullable=False,
    )

    category: Mapped[Category | None] = relationship(
        back_populates="funds",
        lazy="selectin",
    )
    region: Mapped[Region | None] = relationship(
        back_populates="funds",
        lazy="selectin",
    )
    indexes: Mapped[FundIndex | None] = relationship(
        back_populates="fund",
        lazy="selectin",
        uselist=False,
        cascade="all, delete-orphan",
    )
    projects: Mapped[list[Project]] = relationship(
        back_populates="fund",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates="fund",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    complaints: Mapped[list[Complaint]] = relationship(
        back_populates="fund",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list[FinancialReport]] = relationship(
        back_populates="fund",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    users: Mapped[list[User]] = relationship(
        back_populates="fund",
        lazy="selectin",
    )
    news_items: Mapped[list[News]] = relationship(
        back_populates="fund",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    index_scores: Mapped[list[FundIndexScore]] = relationship(
        back_populates="fund",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

