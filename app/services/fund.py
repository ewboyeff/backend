from __future__ import annotations

import math
import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund
from app.models.project import Project
from app.models.report import FinancialReport
from app.repositories.fund import FundRepository
from app.schemas.base import PaginationMeta
from app.schemas.fund import FundCreate, FundUpdate


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    """Convert Uzbek/any text to a URL-safe slug."""
    text = text.lower().strip()
    # Remove characters that are not alphanumeric, spaces, or hyphens
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    # Collapse whitespace and underscores into a single hyphen
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")[:200]


def _make_meta(page: int, per_page: int, total: int) -> PaginationMeta:
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginationMeta(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class FundService:
    def __init__(self, db: AsyncSession) -> None:
        self.fund_repo = FundRepository(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _resolve_slug(
        self, base_slug: str, exclude_id: UUID | None = None
    ) -> str:
        """Return a unique slug, appending -N suffix if needed."""
        slug = base_slug
        counter = 1
        while await self.fund_repo.slug_exists(slug, exclude_id):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def list_funds(
        self,
        page: int = 1,
        per_page: int = 20,
        q: str | None = None,
        category_id: UUID | None = None,
        region_id: UUID | None = None,
        grade: str | None = None,
        status: str | None = None,
        is_verified: bool | None = None,
        sort: str = "newest",
    ) -> tuple[list[Fund], PaginationMeta]:
        skip = (page - 1) * per_page
        funds, total = await self.fund_repo.get_list(
            skip=skip,
            limit=per_page,
            q=q,
            category_id=category_id,
            region_id=region_id,
            grade=grade,
            status=status,
            is_verified=is_verified,
            sort=sort,
        )
        return funds, _make_meta(page, per_page, total)

    async def get_by_slug(self, slug: str) -> Fund:
        fund = await self.fund_repo.get_by_slug(slug)
        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "FUND_NOT_FOUND", "message": "Fond topilmadi"},
            )
        return fund

    async def get_by_id(self, fund_id: UUID) -> Fund:
        fund = await self.fund_repo.get_by_id(fund_id)
        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "FUND_NOT_FOUND", "message": "Fond topilmadi"},
            )
        return fund

    async def create(self, data: FundCreate) -> Fund:
        base_slug = _slugify(data.slug or data.name_uz)
        slug = await self._resolve_slug(base_slug)

        fund_data = data.model_dump(exclude={"slug"})
        fund_data["slug"] = slug

        return await self.fund_repo.create(fund_data)

    async def update(self, fund_id: UUID, data: FundUpdate) -> Fund:
        fund = await self.get_by_id(fund_id)

        update_dict = data.model_dump(exclude_unset=True)

        if "slug" in update_dict and update_dict["slug"]:
            new_slug = _slugify(update_dict["slug"])
            update_dict["slug"] = await self._resolve_slug(
                new_slug, exclude_id=fund_id
            )

        return await self.fund_repo.update(fund, update_dict)

    async def delete(self, fund_id: UUID) -> None:
        deleted = await self.fund_repo.delete(fund_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "FUND_NOT_FOUND", "message": "Fond topilmadi"},
            )

    async def verify(self, fund_id: UUID) -> Fund:
        fund = await self.get_by_id(fund_id)
        return await self.fund_repo.update(fund, {"is_verified": True})

    async def get_projects(
        self, fund_id: UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[Project], PaginationMeta]:
        await self.get_by_id(fund_id)  # raises 404 if not found
        skip = (page - 1) * per_page
        projects, total = await self.fund_repo.get_projects(
            fund_id, skip=skip, limit=per_page
        )
        return projects, _make_meta(page, per_page, total)

    async def get_reports(
        self, fund_id: UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[FinancialReport], PaginationMeta]:
        await self.get_by_id(fund_id)  # raises 404 if not found
        skip = (page - 1) * per_page
        reports, total = await self.fund_repo.get_reports(
            fund_id, skip=skip, limit=per_page
        )
        return reports, _make_meta(page, per_page, total)
