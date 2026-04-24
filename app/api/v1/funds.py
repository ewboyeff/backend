from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.fund import FundStatus
from app.models.index import IndexGrade
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.base import DataResponse, PaginatedResponse
from app.schemas.fund import (
    FinancialReportResponse,
    FundCreate,
    FundDetail,
    FundIndexResponse,
    FundListItem,
    FundUpdate,
    ProjectResponse,
)
from app.services.fund import FundService


class FundSort(str, Enum):
    rating = "rating"
    index = "index"
    name = "name"
    newest = "newest"
    oldest = "oldest"


router = APIRouter(prefix="/funds", tags=["Funds"])


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[FundListItem])
async def list_funds(
    q: str | None = Query(None, description="Nom bo'yicha qidiruv"),
    category_id: UUID | None = Query(None, description="Kategoriya filtri"),
    region_id: UUID | None = Query(None, description="Viloyat filtri"),
    grade: IndexGrade | None = Query(None, description="Indeks darajasi filtri"),
    fund_status: FundStatus | None = Query(
        None, alias="status", description="Fond holati filtri"
    ),
    is_verified: bool | None = Query(None, description="Tasdiqlangan fondlar"),
    sort: FundSort = Query(FundSort.newest, description="Saralash tartibi"),
    page: int = Query(1, ge=1, description="Sahifa raqami"),
    per_page: int = Query(20, ge=1, le=100, description="Sahifadagi elementlar soni"),
    db: AsyncSession = Depends(get_db),
):
    service = FundService(db)
    funds, meta = await service.list_funds(
        page=page,
        per_page=per_page,
        q=q,
        category_id=category_id,
        region_id=region_id,
        grade=grade.value if grade else None,
        status=fund_status.value if fund_status else None,
        is_verified=is_verified,
        sort=sort.value,
    )
    # Batch-count projects for all returned funds (single extra query)
    fund_ids = [f.id for f in funds]
    if fund_ids:
        count_rows = await db.execute(
            sa_select(Project.fund_id, func.count(Project.id).label("cnt"))
            .where(Project.fund_id.in_(fund_ids))
            .group_by(Project.fund_id)
        )
        project_counts: dict[UUID, int] = {row.fund_id: row.cnt for row in count_rows}
    else:
        project_counts = {}

    items: list[FundListItem] = []
    for f in funds:
        item = FundListItem.model_validate(f)
        item.projects_count = project_counts.get(f.id, 0)
        items.append(item)

    return PaginatedResponse(data=items, meta=meta)


@router.get("/{slug}", response_model=DataResponse[FundDetail])
async def get_fund(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    service = FundService(db)
    fund = await service.get_by_slug(slug)
    return DataResponse(data=FundDetail.model_validate(fund))


@router.get("/{fund_id}/index", response_model=DataResponse[FundIndexResponse])
async def get_fund_index(
    fund_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = FundService(db)
    fund = await service.get_by_id(fund_id)
    if not fund.indexes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "INDEX_NOT_FOUND",
                "message": "Bu fond uchun indeks hali hisoblanmagan",
            },
        )
    return DataResponse(data=FundIndexResponse.model_validate(fund.indexes))


@router.get("/{fund_id}/projects", response_model=PaginatedResponse[ProjectResponse])
async def get_fund_projects(
    fund_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = FundService(db)
    projects, meta = await service.get_projects(fund_id, page=page, per_page=per_page)
    return PaginatedResponse(
        data=[ProjectResponse.model_validate(p) for p in projects],
        meta=meta,
    )


@router.get("/{fund_id}/reports", response_model=PaginatedResponse[FinancialReportResponse])
async def get_fund_reports(
    fund_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = FundService(db)
    reports, meta = await service.get_reports(fund_id, page=page, per_page=per_page)
    return PaginatedResponse(
        data=[FinancialReportResponse.model_validate(r) for r in reports],
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[FundDetail],
)
async def create_fund(
    data: FundCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    service = FundService(db)
    fund = await service.create(data)
    return DataResponse(
        message="Fond muvaffaqiyatli qo'shildi",
        data=FundDetail.model_validate(fund),
    )


@router.put("/{fund_id}", response_model=DataResponse[FundDetail])
async def update_fund(
    fund_id: UUID,
    data: FundUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admin: any fund; fund_rep: only their own fund
    if current_user.role == UserRole.admin:
        pass  # allowed
    elif current_user.role == UserRole.fund_rep:
        if current_user.fund_id != fund_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Siz faqat o'z fondingizni tahrirlashingiz mumkin",
                },
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Bu amalni bajarishga ruxsat yo'q",
            },
        )

    service = FundService(db)
    fund = await service.update(fund_id, data)
    return DataResponse(
        message="Fond muvaffaqiyatli yangilandi",
        data=FundDetail.model_validate(fund),
    )


@router.delete("/{fund_id}", response_model=DataResponse[None])
async def delete_fund(
    fund_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    service = FundService(db)
    await service.delete(fund_id)
    return DataResponse(message="Fond muvaffaqiyatli o'chirildi", data=None)


@router.post("/{fund_id}/verify", response_model=DataResponse[FundDetail])
async def verify_fund(
    fund_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    service = FundService(db)
    fund = await service.verify(fund_id)
    return DataResponse(
        message="Fond muvaffaqiyatli tasdiqlandi",
        data=FundDetail.model_validate(fund),
    )
