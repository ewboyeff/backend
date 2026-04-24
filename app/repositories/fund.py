from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.fund import Fund, FundStatus
from app.models.index import FundIndex, IndexGrade
from app.models.project import Project
from app.models.report import FinancialReport
from app.repositories.base import BaseRepository


class FundRepository(BaseRepository[Fund]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Fund, db)

    async def get_by_slug(self, slug: str) -> Fund | None:
        result = await self.db.execute(
            select(Fund).where(Fund.slug == slug)
        )
        return result.scalar_one_or_none()

    async def slug_exists(
        self, slug: str, exclude_id: UUID | None = None
    ) -> bool:
        stmt = select(Fund.id).where(Fund.slug == slug)
        if exclude_id:
            stmt = stmt.where(Fund.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_list(
        self,
        skip: int = 0,
        limit: int = 20,
        q: str | None = None,
        category_id: UUID | None = None,
        region_id: UUID | None = None,
        grade: str | None = None,
        status: str | None = None,
        is_verified: bool | None = None,
        sort: str = "newest",
    ) -> tuple[list[Fund], int]:
        # Skip heavy relationships that are not needed for list cards
        _noload_opts = [
            noload(Fund.projects),
            noload(Fund.reviews),
            noload(Fund.complaints),
            noload(Fund.reports),
            noload(Fund.users),
            noload(Fund.news_items),
            noload(Fund.index_scores),
        ]

        stmt = select(Fund).options(*_noload_opts)
        count_stmt = select(func.count(Fund.id))

        conditions: list = []

        # Decide whether we need to join fund_indexes
        need_index_join = (grade is not None) or (sort in ("rating", "index"))

        if need_index_join:
            if grade is not None:
                # Inner join: only funds that have an index matching the grade
                stmt = stmt.join(FundIndex, FundIndex.fund_id == Fund.id)
                count_stmt = count_stmt.join(FundIndex, FundIndex.fund_id == Fund.id)
            else:
                # Left outer join: all funds, sorted by score (NULL last)
                stmt = stmt.outerjoin(FundIndex, FundIndex.fund_id == Fund.id)
                count_stmt = count_stmt.outerjoin(FundIndex, FundIndex.fund_id == Fund.id)

        # Search filter
        if q:
            search = f"%{q}%"
            conditions.append(
                or_(
                    Fund.name_uz.ilike(search),
                    Fund.name_ru.ilike(search),
                    Fund.name_en.ilike(search),
                )
            )

        if category_id:
            conditions.append(Fund.category_id == category_id)

        if region_id:
            conditions.append(Fund.region_id == region_id)

        if status:
            conditions.append(Fund.status == status)

        if is_verified is not None:
            conditions.append(Fund.is_verified == is_verified)

        if grade is not None:
            conditions.append(FundIndex.grade == grade)

        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        # Sorting
        if sort in ("rating", "index"):
            stmt = stmt.order_by(FundIndex.overall_score.desc().nullslast())
        elif sort == "name":
            stmt = stmt.order_by(Fund.name_uz.asc())
        elif sort == "oldest":
            stmt = stmt.order_by(Fund.created_at.asc())
        else:  # newest (default)
            stmt = stmt.order_by(Fund.created_at.desc())

        stmt = stmt.offset(skip).limit(limit)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        result = await self.db.execute(stmt)
        funds = list(result.scalars().unique().all())

        return funds, total

    async def get_projects(
        self, fund_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Project], int]:
        count_stmt = select(func.count(Project.id)).where(
            Project.fund_id == fund_id
        )
        stmt = (
            select(Project)
            .where(Project.fund_id == fund_id)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        result = await self.db.execute(stmt)
        projects = list(result.scalars().all())

        return projects, total

    async def get_reports(
        self, fund_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[FinancialReport], int]:
        count_stmt = select(func.count(FinancialReport.id)).where(
            FinancialReport.fund_id == fund_id
        )
        stmt = (
            select(FinancialReport)
            .where(FinancialReport.fund_id == fund_id)
            .order_by(FinancialReport.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        result = await self.db.execute(stmt)
        reports = list(result.scalars().all())

        return reports, total
