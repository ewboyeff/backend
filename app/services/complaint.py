from __future__ import annotations

import math
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint, ComplaintStatus
from app.repositories.complaint import ComplaintRepository
from app.schemas.base import PaginationMeta
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate


def _make_meta(page: int, per_page: int, total: int) -> PaginationMeta:
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginationMeta(page=page, per_page=per_page, total=total, total_pages=total_pages)


class ComplaintService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ComplaintRepository(db)

    async def create(
        self, fund_id: UUID, user_id: UUID, data: ComplaintCreate
    ) -> Complaint:
        return await self.repo.create(
            fund_id=fund_id,
            user_id=user_id,
            reason=data.reason,
            description=data.description,
        )

    async def get_list(
        self,
        page: int = 1,
        per_page: int = 20,
        status: ComplaintStatus | None = None,
        fund_id: UUID | None = None,
    ) -> tuple[list[Complaint], PaginationMeta]:
        skip = (page - 1) * per_page
        complaints, total = await self.repo.get_list(
            status=status,
            fund_id=fund_id,
            skip=skip,
            limit=per_page,
        )
        return complaints, _make_meta(page, per_page, total)

    async def update(self, complaint_id: UUID, data: ComplaintUpdate) -> Complaint:
        complaint = await self.repo.get_by_id(complaint_id)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "COMPLAINT_NOT_FOUND", "message": "Shikoyat topilmadi"},
            )
        update_dict = data.model_dump(exclude_unset=True)
        return await self.repo.update(complaint, update_dict)
