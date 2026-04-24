from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.models.application import Application
from app.models.user import UserRole
from app.schemas.application import ApplicationCreate, ApplicationResponse
from app.schemas.base import DataResponse, PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[ApplicationResponse],
)
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Hamkorlik murojaatini yuborish (autentifikatsiya talab qilinmaydi)."""
    app = Application(
        type=data.type,
        full_name=data.full_name,
        organization=data.organization,
        phone=data.phone,
        email=data.email,
        message=data.message,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return DataResponse(
        message="Murojaatingiz muvaffaqiyatli yuborildi",
        data=ApplicationResponse.model_validate(app),
    )


@router.get(
    "",
    response_model=PaginatedResponse[ApplicationResponse],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def list_applications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Murojaatlar ro'yxati (moderator/admin)."""
    offset = (page - 1) * per_page

    total_result = await db.execute(select(func.count()).select_from(Application))
    total = total_result.scalar_one()

    result = await db.execute(
        select(Application).order_by(Application.created_at.desc()).offset(offset).limit(per_page)
    )
    apps = result.scalars().all()

    return PaginatedResponse(
        data=[ApplicationResponse.model_validate(a) for a in apps],
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page,
        ),
    )
