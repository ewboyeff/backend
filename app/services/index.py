from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund
from app.models.index import FundIndex, IndexFactor, IndexGrade, IndexType
from app.repositories.index import IndexRepository
from app.schemas.base import PaginationMeta
from app.schemas.index import (
    FundIndexCalcResponse,
    FundIndexScoreItem,
    IndexCalculateRequest,
    IndexFactorUpdate,
    IndexFactorsGrouped,
)

# ---------------------------------------------------------------------------
# Grade formula (TZ 2.4)
#   90-100 → Platinum
#   75-89  → Gold
#   60-74  → Silver
#   45-59  → Bronze
#   0-44   → Unrated
# ---------------------------------------------------------------------------

def _score_to_grade(score: Decimal) -> IndexGrade:
    if score >= 90:
        return IndexGrade.platinum
    elif score >= 75:
        return IndexGrade.gold
    elif score >= 60:
        return IndexGrade.silver
    elif score >= 45:
        return IndexGrade.bronze
    else:
        return IndexGrade.unrated


def _make_meta(page: int, per_page: int, total: int) -> PaginationMeta:
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginationMeta(
        page=page, per_page=per_page, total=total, total_pages=total_pages
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class IndexService:
    def __init__(self, db: AsyncSession) -> None:
        self.idx_repo = IndexRepository(db)

    async def get_factors_grouped(self) -> IndexFactorsGrouped:
        """Return all active factors grouped by index type."""
        factors = await self.idx_repo.get_active_factors()
        grouped: dict[str, list] = {
            "transparency": [],
            "openness": [],
            "trust": [],
        }
        for f in factors:
            grouped[f.index_type.value].append(f)
        return IndexFactorsGrouped(**grouped)

    async def calculate(
        self,
        fund_id: UUID,
        data: IndexCalculateRequest,
    ) -> FundIndexCalcResponse:
        """
        1. Validate & save individual factor scores.
        2. Compute weighted sums per index type.
        3. Apply TZ overall formula: T×40% + O×30% + I×30%.
        4. Determine grade, persist FundIndex.
        5. Return full result with per-factor breakdown.
        """
        # -- Fetch all active factors -------------------------------------------
        all_factors: list[IndexFactor] = await self.idx_repo.get_active_factors()
        factor_map: dict[UUID, IndexFactor] = {f.id: f for f in all_factors}

        # -- Validate submitted factor IDs ----------------------------------------
        for item in data.scores:
            if item.factor_id not in factor_map:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "FACTOR_NOT_FOUND",
                        "message": f"Omil topilmadi: {item.factor_id}",
                    },
                )

        # -- Persist submitted scores ---------------------------------------------
        for item in data.scores:
            await self.idx_repo.upsert_fund_score(
                fund_id=fund_id,
                factor_id=item.factor_id,
                score=item.score,
                note=item.note,
            )

        # -- Load ALL stored scores for this fund ---------------------------------
        all_stored = await self.idx_repo.get_fund_scores(fund_id)
        score_map: dict[UUID, Decimal] = {s.factor_id: s.score for s in all_stored}
        note_map: dict[UUID, str | None] = {s.factor_id: s.note for s in all_stored}

        # -- Calculate weighted sum per index type --------------------------------
        # Each factor's contribution = (factor_score × factor_weight) / 100
        # The weights within each type sum to 100, so the result is 0–100.
        type_totals: dict[IndexType, Decimal] = {
            IndexType.transparency: Decimal("0"),
            IndexType.openness: Decimal("0"),
            IndexType.trust: Decimal("0"),
        }

        for factor in all_factors:
            score = score_map.get(factor.id, Decimal("0"))
            contribution = (score * factor.weight / Decimal("100")).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            type_totals[factor.index_type] += contribution

        TWO_PLACES = Decimal("0.01")
        transparency = type_totals[IndexType.transparency].quantize(TWO_PLACES, ROUND_HALF_UP)
        openness = type_totals[IndexType.openness].quantize(TWO_PLACES, ROUND_HALF_UP)
        trust = type_totals[IndexType.trust].quantize(TWO_PLACES, ROUND_HALF_UP)

        # -- Overall formula (TZ 2.4): T×40% + O×30% + I×30% -------------------
        overall = (
            transparency * Decimal("0.40")
            + openness * Decimal("0.30")
            + trust * Decimal("0.30")
        ).quantize(TWO_PLACES, ROUND_HALF_UP)

        grade = _score_to_grade(overall)

        # -- Persist FundIndex record --------------------------------------------
        fund_index: FundIndex = await self.idx_repo.upsert_fund_index(
            fund_id=fund_id,
            transparency_score=transparency,
            openness_score=openness,
            trust_score=trust,
            overall_score=overall,
            grade=grade,
        )

        # -- Build per-factor breakdown for response ----------------------------
        factor_scores: list[FundIndexScoreItem] = [
            FundIndexScoreItem(
                factor_id=factor.id,
                index_type=factor.index_type,
                factor_name_uz=factor.name_uz,
                weight=factor.weight,
                score=score_map.get(factor.id, Decimal("0")),
                note=note_map.get(factor.id),
            )
            for factor in all_factors
        ]

        return FundIndexCalcResponse(
            fund_id=fund_index.fund_id,
            transparency_score=fund_index.transparency_score,
            openness_score=fund_index.openness_score,
            trust_score=fund_index.trust_score,
            overall_score=fund_index.overall_score,
            grade=fund_index.grade,
            calculated_at=fund_index.calculated_at,
            factor_scores=factor_scores,
        )

    async def get_ranking(
        self,
        page: int = 1,
        per_page: int = 20,
        category_id: UUID | None = None,
        region_id: UUID | None = None,
        grade: str | None = None,
    ) -> tuple[list[Fund], PaginationMeta]:
        skip = (page - 1) * per_page
        funds, total = await self.idx_repo.get_ranking(
            skip=skip,
            limit=per_page,
            category_id=category_id,
            region_id=region_id,
            grade=grade,
        )
        return funds, _make_meta(page, per_page, total)

    async def update_factor(
        self, factor_id: UUID, data: IndexFactorUpdate
    ) -> IndexFactor:
        update_dict = data.model_dump(exclude_unset=True)
        factor = await self.idx_repo.update_factor(factor_id, update_dict)
        if not factor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "FACTOR_NOT_FOUND",
                    "message": "Indeks omili topilmadi",
                },
            )
        return factor
