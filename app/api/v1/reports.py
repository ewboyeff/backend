from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_role
from app.models.report import FinancialReport
from app.models.user import UserRole
from app.schemas.base import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.report import ReportCreate, ReportResponse, ReportUpdate

router = APIRouter(prefix="/reports", tags=["Reports"])

_admin = [Depends(require_role(UserRole.moderator, UserRole.admin))]


@router.get("", response_model=PaginatedResponse[ReportResponse])
async def list_reports(
    page: int = 1,
    per_page: int = 20,
    fund_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if fund_id:
        conditions.append(FinancialReport.fund_id == fund_id)

    count_stmt = select(func.count(FinancialReport.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * per_page
    data_stmt = (
        select(FinancialReport)
        .options(selectinload(FinancialReport.fund))
        .order_by(FinancialReport.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    if conditions:
        data_stmt = data_stmt.where(*conditions)
    reports = (await db.execute(data_stmt)).scalars().all()

    return PaginatedResponse(
        data=[ReportResponse.model_validate(r) for r in reports],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=max(1, -(-total // per_page)),
        ),
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DataResponse[ReportResponse], dependencies=_admin)
async def create_report(data: ReportCreate, db: AsyncSession = Depends(get_db)):
    report = FinancialReport(**data.model_dump())
    db.add(report)
    await db.commit()
    await db.refresh(report)
    result = await db.execute(
        select(FinancialReport).where(FinancialReport.id == report.id).options(selectinload(FinancialReport.fund))
    )
    report = result.scalar_one()
    return DataResponse(message="Hisobot qo'shildi", data=ReportResponse.model_validate(report))


@router.put("/{report_id}", response_model=DataResponse[ReportResponse], dependencies=_admin)
async def update_report(report_id: UUID, data: ReportUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FinancialReport).where(FinancialReport.id == report_id).options(selectinload(FinancialReport.fund))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Hisobot topilmadi"})

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(report, field, value)
    await db.commit()
    await db.refresh(report)
    return DataResponse(message="Hisobot yangilandi", data=ReportResponse.model_validate(report))


@router.patch("/{report_id}/verify", response_model=DataResponse[ReportResponse], dependencies=_admin)
async def toggle_verify(report_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FinancialReport).where(FinancialReport.id == report_id).options(selectinload(FinancialReport.fund))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Hisobot topilmadi"})

    report.is_verified = not report.is_verified
    await db.commit()
    await db.refresh(report)
    return DataResponse(message="Hisobot holati yangilandi", data=ReportResponse.model_validate(report))


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_admin)
async def delete_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FinancialReport).where(FinancialReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Hisobot topilmadi"})
    await db.delete(report)
    await db.commit()
