from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.index import IndexGrade, IndexType


# ---------------------------------------------------------------------------
# IndexFactor schemas
# ---------------------------------------------------------------------------


class IndexFactorResponse(BaseModel):
    id: UUID
    index_type: IndexType
    name_uz: str
    name_ru: str | None
    name_en: str | None
    weight: Decimal
    is_active: bool
    order: int

    model_config = ConfigDict(from_attributes=True)


class IndexFactorsGrouped(BaseModel):
    """Factors grouped by index type."""
    transparency: list[IndexFactorResponse]
    openness: list[IndexFactorResponse]
    trust: list[IndexFactorResponse]


class IndexFactorCreate(BaseModel):
    index_type: IndexType
    name_uz: str
    name_ru: str | None = None
    name_en: str | None = None
    weight: Decimal = Field(ge=0, le=100)
    order: int = 0


class IndexFactorUpdate(BaseModel):
    """Admin can update factor metadata and weight."""
    name_uz: str | None = None
    name_ru: str | None = None
    name_en: str | None = None
    weight: Decimal | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None
    order: int | None = None


# ---------------------------------------------------------------------------
# Calculation request/response
# ---------------------------------------------------------------------------


class FactorScoreInput(BaseModel):
    """A single factor score provided by admin."""
    factor_id: UUID
    score: Decimal = Field(ge=0, le=100, description="Ball (0–100)")
    note: str | None = None


class IndexCalculateRequest(BaseModel):
    """
    Admin sends individual factor scores.
    Missing factors keep their existing score (or 0 if never set).
    """
    scores: list[FactorScoreInput]


class FundIndexScoreItem(BaseModel):
    """Detailed view of one factor score for a fund."""
    factor_id: UUID
    index_type: IndexType
    factor_name_uz: str
    weight: Decimal
    score: Decimal
    note: str | None

    model_config = ConfigDict(from_attributes=True)


class FundIndexCalcResponse(BaseModel):
    """Full result returned after index calculation."""
    fund_id: UUID
    transparency_score: Decimal
    openness_score: Decimal
    trust_score: Decimal
    overall_score: Decimal
    grade: IndexGrade
    calculated_at: datetime | None
    factor_scores: list[FundIndexScoreItem]

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Ranking item
# ---------------------------------------------------------------------------


class RankingItem(BaseModel):
    """A fund entry in the ranking list, with its position."""
    rank: int
    fund_id: UUID
    name_uz: str
    name_ru: str | None
    name_en: str | None
    slug: str
    logo_url: str | None
    logo_initials: str | None
    logo_color: str | None
    is_verified: bool
    transparency_score: Decimal
    openness_score: Decimal
    trust_score: Decimal
    overall_score: Decimal
    grade: IndexGrade

    model_config = ConfigDict(from_attributes=True)
