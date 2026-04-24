from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.complaint import ComplaintStatus
from app.models.user import User, UserRole
from app.schemas.base import DataResponse, PaginatedResponse
from app.schemas.complaint import ComplaintCreate, ComplaintResponse, ComplaintUpdate
from app.services.complaint import ComplaintService

router = APIRouter(prefix="/funds", tags=["Complaints"])
complaints_router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "/{fund_id}/complaints",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[ComplaintResponse],
)
async def create_complaint(
    fund_id: UUID,
    data: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fond haqida shikoyat yuborish (autentifikatsiya talab qilinadi).
    """
    service = ComplaintService(db)
    complaint = await service.create(fund_id=fund_id, user_id=current_user.id, data=data)
    return DataResponse(
        message="Shikoyat muvaffaqiyatli yuborildi",
        data=ComplaintResponse.model_validate(complaint),
    )


@complaints_router.get(
    "",
    response_model=PaginatedResponse[ComplaintResponse],
)
async def list_complaints(
    status_filter: ComplaintStatus | None = Query(None, alias="status"),
    fund_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.moderator, UserRole.admin)),
):
    """
    Shikoyatlar ro'yxati (moderator/admin).
    """
    service = ComplaintService(db)
    complaints, meta = await service.get_list(
        page=page,
        per_page=per_page,
        status=status_filter,
        fund_id=fund_id,
    )
    return PaginatedResponse(
        data=[ComplaintResponse.from_orm_with_user(c) for c in complaints],
        meta=meta,
    )


@complaints_router.put(
    "/{complaint_id}",
    response_model=DataResponse[ComplaintResponse],
)
async def update_complaint(
    complaint_id: UUID,
    data: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.moderator, UserRole.admin)),
):
    """
    Shikoyat holatini yangilash (moderator/admin).
    """
    service = ComplaintService(db)
    complaint = await service.update(complaint_id, data)
    return DataResponse(
        message="Shikoyat yangilandi",
        data=ComplaintResponse.model_validate(complaint),
    )
