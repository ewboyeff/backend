from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.models.partner import Partner
from app.models.user import UserRole
from app.schemas.base import DataResponse
from app.schemas.partner import PartnerCreate, PartnerResponse, PartnerUpdate

router = APIRouter(prefix="/partners", tags=["Partners"])


@router.get("", response_model=DataResponse[list[PartnerResponse]])
async def list_partners(db: AsyncSession = Depends(get_db)):
    """Faol hamkorlar ro'yxati (hamma uchun ochiq)."""
    result = await db.execute(
        select(Partner).where(Partner.is_active == True).order_by(Partner.order_index, Partner.created_at)
    )
    partners = result.scalars().all()
    return DataResponse(data=[PartnerResponse.model_validate(p) for p in partners])


@router.get(
    "/all",
    response_model=DataResponse[list[PartnerResponse]],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def list_all_partners(db: AsyncSession = Depends(get_db)):
    """Barcha hamkorlar (admin)."""
    result = await db.execute(
        select(Partner).order_by(Partner.order_index, Partner.created_at)
    )
    partners = result.scalars().all()
    return DataResponse(data=[PartnerResponse.model_validate(p) for p in partners])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[PartnerResponse],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def create_partner(data: PartnerCreate, db: AsyncSession = Depends(get_db)):
    partner = Partner(**data.model_dump())
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return DataResponse(message="Hamkor qo'shildi", data=PartnerResponse.model_validate(partner))


@router.put(
    "/{partner_id}",
    response_model=DataResponse[PartnerResponse],
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def update_partner(partner_id: UUID, data: PartnerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Hamkor topilmadi"})

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(partner, field, value)
    await db.commit()
    await db.refresh(partner)
    return DataResponse(message="Hamkor yangilandi", data=PartnerResponse.model_validate(partner))


@router.delete(
    "/{partner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(UserRole.moderator, UserRole.admin))],
)
async def delete_partner(partner_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Hamkor topilmadi"})
    await db.delete(partner)
    await db.commit()
