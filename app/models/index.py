from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.fund import Fund


class IndexGrade(str, Enum):
    platinum = "platinum"
    gold = "gold"
    silver = "silver"
    bronze = "bronze"
    unrated = "unrated"


class IndexType(str, Enum):
    transparency = "transparency"
    openness = "openness"
    trust = "trust"


class FundIndex(Base):
    __tablename__ = "fund_indexes"

    fund_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("funds.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    transparency_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    openness_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    trust_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    grade: Mapped[IndexGrade] = mapped_column(
        SQLEnum(IndexGrade, name="index_grade"),
        default=IndexGrade.unrated,
        nullable=False,
    )
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    fund: Mapped[Fund] = relationship(
        back_populates="indexes",
        lazy="selectin",
    )


class IndexFactor(Base):
    __tablename__ = "index_factors"

    index_type: Mapped[IndexType] = mapped_column(
        SQLEnum(IndexType, name="index_type"),
        nullable=False,
    )
    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    scores: Mapped[list[FundIndexScore]] = relationship(
        back_populates="factor",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class FundIndexScore(Base):
    __tablename__ = "fund_index_scores"
    __table_args__ = (
        UniqueConstraint("fund_id", "factor_id", name="uq_fund_index_scores_fund_factor"),
    )

    fund_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("funds.id", ondelete="CASCADE"),
        nullable=False,
    )
    factor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("index_factors.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    fund: Mapped[Fund] = relationship(
        back_populates="index_scores",
        lazy="selectin",
    )
    factor: Mapped[IndexFactor] = relationship(
        back_populates="scores",
        lazy="selectin",
    )

