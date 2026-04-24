from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.report import ReportType


class ReportCreate(BaseModel):
    fund_id: UUID
    report_type: ReportType
    period_start: date | None = None
    period_end: date | None = None
    total_income: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_expense: Decimal = Field(default=Decimal("0.00"), ge=0)
    file_url: str | None = Field(default=None, max_length=500)
    is_verified: bool = False


class ReportUpdate(BaseModel):
    fund_id: UUID | None = None
    report_type: ReportType | None = None
    period_start: date | None = None
    period_end: date | None = None
    total_income: Decimal | None = Field(default=None, ge=0)
    total_expense: Decimal | None = Field(default=None, ge=0)
    file_url: str | None = None
    is_verified: bool | None = None


class FundShort(BaseModel):
    id: UUID
    name_uz: str
    logo_initials: str | None
    logo_color: str | None

    model_config = ConfigDict(from_attributes=True)


class ReportResponse(BaseModel):
    id: UUID
    fund_id: UUID
    fund: FundShort | None = None
    report_type: ReportType
    period_start: date | None
    period_end: date | None
    total_income: Decimal
    total_expense: Decimal
    file_url: str | None
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
