from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.models.project import Project, ProjectStatus
from app.models.user import UserRole
from app.schemas.base import DataResponse, PaginatedResponse, PaginationMeta
from app.schemas.fund import ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    fund_id: UUID
    title_uz: str = Field(min_length=1, max_length=255)
    title_ru: str | None = None
    title_en: str | None = None
    description_uz: str | None = None
    status: ProjectStatus = ProjectStatus.planned
    budget: Decimal = Decimal("0")
    spent: Decimal = Decimal("0")
    currency: str = "UZS"
    beneficiaries_count: int = 0
    start_date: date | None = None
    end_date: date | None = None


class ProjectUpdate(BaseModel):
    title_uz: str | None = Field(default=None, min_length=1, max_length=255)
    title_ru: str | None = None
    title_en: str | None = None
    description_uz: str | None = None
    status: ProjectStatus | None = None
    budget: Decimal | None = None
    spent: Decimal | None = None
    beneficiaries_count: int | None = None
    start_date: date | None = None
    end_date: date | None = None


def _make_meta(page: int, per_page: int, total: int) -> PaginationMeta:
    import math
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginationMeta(page=page, per_page=per_page, total=total, total_pages=total_pages)


@router.get(
    "",
    response_model=PaginatedResponse[ProjectResponse],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def list_projects(
    fund_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Project)
    count_query = select(func.count()).select_from(Project)
    if fund_id:
        query = query.where(Project.fund_id == fund_id)
        count_query = count_query.where(Project.fund_id == fund_id)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    projects = result.scalars().all()
    return PaginatedResponse(
        data=[ProjectResponse.model_validate(p) for p in projects],
        meta=_make_meta(page, per_page, total),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[ProjectResponse],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(**data.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    # reload with relationships
    result = await db.execute(select(Project).where(Project.id == project.id))
    project = result.scalar_one()
    return DataResponse(message="Loyiha qo'shildi", data=ProjectResponse.model_validate(project))


@router.put(
    "/{project_id}",
    response_model=DataResponse[ProjectResponse],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def update_project(project_id: UUID, data: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Loyiha topilmadi"})
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one()
    return DataResponse(message="Loyiha yangilandi", data=ProjectResponse.model_validate(project))


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def delete_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Loyiha topilmadi"})
    await db.delete(project)
    await db.commit()
