from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.fund import Fund, FundStatus
from app.models.index import FundIndex, FundIndexScore, IndexFactor, IndexGrade, IndexType


class IndexRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # IndexFactor
    # ------------------------------------------------------------------

    async def get_active_factors(
        self, index_type: IndexType | None = None
    ) -> list[IndexFactor]:
        stmt = select(IndexFactor).where(IndexFactor.is_active == True)  # noqa: E712
        if index_type:
            stmt = stmt.where(IndexFactor.index_type == index_type)
        stmt = stmt.order_by(IndexFactor.index_type, IndexFactor.order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_factor_by_id(self, factor_id: UUID) -> IndexFactor | None:
        result = await self.db.execute(
            select(IndexFactor).where(IndexFactor.id == factor_id)
        )
        return result.scalar_one_or_none()

    async def update_factor(
        self, factor_id: UUID, update_dict: dict
    ) -> IndexFactor | None:
        factor = await self.get_factor_by_id(factor_id)
        if not factor:
            return None
        for key, value in update_dict.items():
            setattr(factor, key, value)
        self.db.add(factor)
        await self.db.flush()
        await self.db.refresh(factor)
        return factor

    # ------------------------------------------------------------------
    # FundIndexScore (per-factor scores for a fund)
    # ------------------------------------------------------------------

    async def get_fund_scores(self, fund_id: UUID) -> list[FundIndexScore]:
        result = await self.db.execute(
            select(FundIndexScore).where(FundIndexScore.fund_id == fund_id)
        )
        return list(result.scalars().all())

    async def upsert_fund_score(
        self,
        fund_id: UUID,
        factor_id: UUID,
        score: Decimal,
        note: str | None = None,
    ) -> FundIndexScore:
        """Create or update a single factor score for a fund."""
        result = await self.db.execute(
            select(FundIndexScore).where(
                FundIndexScore.fund_id == fund_id,
                FundIndexScore.factor_id == factor_id,
            )
        )
        existing = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if existing:
            existing.score = score
            existing.note = note
            existing.calculated_at = now
            self.db.add(existing)
        else:
            existing = FundIndexScore(
                fund_id=fund_id,
                factor_id=factor_id,
                score=score,
                note=note,
                calculated_at=now,
            )
            self.db.add(existing)

        await self.db.flush()
        await self.db.refresh(existing)
        return existing

    # ------------------------------------------------------------------
    # FundIndex (overall index record)
    # ------------------------------------------------------------------

    async def get_fund_index(self, fund_id: UUID) -> FundIndex | None:
        result = await self.db.execute(
            select(FundIndex).where(FundIndex.fund_id == fund_id)
        )
        return result.scalar_one_or_none()

    async def upsert_fund_index(
        self,
        fund_id: UUID,
        transparency_score: Decimal,
        openness_score: Decimal,
        trust_score: Decimal,
        overall_score: Decimal,
        grade: IndexGrade,
    ) -> FundIndex:
        """Create or update the overall FundIndex record."""
        existing = await self.get_fund_index(fund_id)
        now = datetime.now(timezone.utc)

        if existing:
            existing.transparency_score = transparency_score
            existing.openness_score = openness_score
            existing.trust_score = trust_score
            existing.overall_score = overall_score
            existing.grade = grade
            existing.calculated_at = now
            self.db.add(existing)
        else:
            existing = FundIndex(
                fund_id=fund_id,
                transparency_score=transparency_score,
                openness_score=openness_score,
                trust_score=trust_score,
                overall_score=overall_score,
                grade=grade,
                calculated_at=now,
            )
            self.db.add(existing)

        await self.db.flush()
        await self.db.refresh(existing)
        return existing

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    async def get_ranking(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: UUID | None = None,
        region_id: UUID | None = None,
        grade: str | None = None,
    ) -> tuple[list[Fund], int]:
        """Return funds sorted by overall_score DESC (only active funds with indexes)."""
        _noload_opts = [
            noload(Fund.projects),
            noload(Fund.reviews),
            noload(Fund.complaints),
            noload(Fund.reports),
            noload(Fund.users),
            noload(Fund.news_items),
            noload(Fund.index_scores),
        ]

        # Inner join: only funds that have a FundIndex entry
        stmt = (
            select(Fund)
            .options(*_noload_opts)
            .join(FundIndex, FundIndex.fund_id == Fund.id)
            .where(Fund.status == FundStatus.active)
        )
        count_stmt = (
            select(func.count(Fund.id))
            .join(FundIndex, FundIndex.fund_id == Fund.id)
            .where(Fund.status == FundStatus.active)
        )

        conditions: list = []

        if category_id:
            conditions.append(Fund.category_id == category_id)
        if region_id:
            conditions.append(Fund.region_id == region_id)
        if grade:
            conditions.append(FundIndex.grade == grade)

        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        stmt = (
            stmt.order_by(FundIndex.overall_score.desc())
            .offset(skip)
            .limit(limit)
        )

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        result = await self.db.execute(stmt)
        funds = list(result.scalars().unique().all())

        return funds, total
