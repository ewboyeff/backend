from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.fund import FundStatus
from app.models.index import IndexGrade
from app.models.project import ProjectStatus
from app.models.report import ReportType


# ---------------------------------------------------------------------------
# Nested / short schemas
# ---------------------------------------------------------------------------


class CategoryShort(BaseModel):
    id: UUID
    name_uz: str
    name_ru: str | None
    name_en: str | None
    slug: str

    model_config = ConfigDict(from_attributes=True)


class RegionShort(BaseModel):
    id: UUID
    name_uz: str
    name_ru: str | None
    name_en: str | None
    code: str

    model_config = ConfigDict(from_attributes=True)


class FundIndexResponse(BaseModel):
    transparency_score: Decimal
    openness_score: Decimal
    trust_score: Decimal
    overall_score: Decimal
    grade: IndexGrade
    calculated_at: datetime | None
    valid_until: datetime | None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Fund list / detail schemas
# ---------------------------------------------------------------------------


class FundListItem(BaseModel):
    id: UUID
    name_uz: str
    name_ru: str | None
    name_en: str | None
    slug: str
    logo_url: str | None
    logo_initials: str | None
    logo_color: str | None
    is_verified: bool
    is_active: bool
    status: FundStatus
    founded_year: int | None
    category: CategoryShort | None
    region: RegionShort | None
    indexes: FundIndexResponse | None
    created_at: datetime
    projects_count: int = 0
    donation_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FundDetail(FundListItem):
    description_uz: str | None
    description_ru: str | None
    description_en: str | None
    director_name: str | None
    legal_address: str | None
    inn: str | None
    registration_number: str | None
    website_url: str | None
    telegram_url: str | None
    instagram_url: str | None
    donation_url: str | None
    updated_at: datetime


# ---------------------------------------------------------------------------
# Fund create / update schemas
# ---------------------------------------------------------------------------


class FundCreate(BaseModel):
    name_uz: str
    name_ru: str | None = None
    name_en: str | None = None
    slug: str | None = None  # auto-generated from name_uz if omitted
    description_uz: str | None = None
    description_ru: str | None = None
    description_en: str | None = None
    logo_url: str | None = None
    logo_initials: str | None = None
    logo_color: str | None = None
    director_name: str | None = None
    founded_year: int | None = None
    legal_address: str | None = None
    inn: str | None = None
    registration_number: str | None = None
    category_id: UUID | None = None
    region_id: UUID | None = None
    website_url: str | None = None
    telegram_url: str | None = None
    instagram_url: str | None = None
    donation_url: str | None = None
    status: FundStatus = FundStatus.active


class FundUpdate(BaseModel):
    name_uz: str | None = None
    name_ru: str | None = None
    name_en: str | None = None
    slug: str | None = None
    description_uz: str | None = None
    description_ru: str | None = None
    description_en: str | None = None
    logo_url: str | None = None
    logo_initials: str | None = None
    logo_color: str | None = None
    director_name: str | None = None
    founded_year: int | None = None
    legal_address: str | None = None
    inn: str | None = None
    registration_number: str | None = None
    category_id: UUID | None = None
    region_id: UUID | None = None
    website_url: str | None = None
    telegram_url: str | None = None
    instagram_url: str | None = None
    donation_url: str | None = None
    status: FundStatus | None = None


# ---------------------------------------------------------------------------
# Sub-resource schemas (projects, reports)
# ---------------------------------------------------------------------------


class ProjectResponse(BaseModel):
    id: UUID
    fund_id: UUID
    title_uz: str
    title_ru: str | None
    title_en: str | None
    description_uz: str | None
    description_ru: str | None
    description_en: str | None
    status: ProjectStatus
    budget: Decimal
    spent: Decimal
    currency: str
    beneficiaries_count: int
    start_date: date | None
    end_date: date | None
    region: RegionShort | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinancialReportResponse(BaseModel):
    id: UUID
    fund_id: UUID
    report_type: ReportType
    period_start: date | None
    period_end: date | None
    total_income: Decimal
    total_expense: Decimal
    file_url: str | None
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
