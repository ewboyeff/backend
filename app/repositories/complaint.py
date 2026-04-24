from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint, ComplaintStatus


class ComplaintRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, complaint_id: UUID) -> Complaint | None:
        result = await self.db.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        fund_id: UUID,
        user_id: UUID,
        reason: str,
        description: str | None,
    ) -> Complaint:
        complaint = Complaint(
            fund_id=fund_id,
            user_id=user_id,
            reason=reason,
            description=description,
            status=ComplaintStatus.pending,
        )
        self.db.add(complaint)
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint

    async def get_list(
        self,
        status: ComplaintStatus | None = None,
        fund_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Complaint], int]:
        stmt = select(Complaint)
        count_stmt = select(func.count(Complaint.id))

        conditions = []
        if status:
            conditions.append(Complaint.status == status)
        if fund_id:
            conditions.append(Complaint.fund_id == fund_id)

        if conditions:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        stmt = stmt.order_by(Complaint.created_at.desc()).offset(skip).limit(limit)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def update(self, complaint: Complaint, update_dict: dict) -> Complaint:
        for key, value in update_dict.items():
            setattr(complaint, key, value)
        self.db.add(complaint)
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint
