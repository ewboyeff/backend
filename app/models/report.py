from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum as SQLEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.fund import Fund


class ReportType(str, Enum):
    annual = "annual"
    quarterly = "quarterly"
    monthly = "monthly"


class FinancialReport(Base):
    __tablename__ = "financial_reports"

    fund_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("funds.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_type: Mapped[ReportType] = mapped_column(
        SQLEnum(ReportType, name="report_type"),
        nullable=False,
    )
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_income: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_expense: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    fund: Mapped[Fund] = relationship(
        back_populates="reports",
        lazy="selectin",
    )

