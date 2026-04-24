from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.models.index import IndexGrade
from app.models.user import User, UserRole
from app.schemas.base import DataResponse, PaginatedResponse
from app.schemas.fund import FundListItem
from app.schemas.index import (
    FundIndexCalcResponse,
    FundIndexScoreItem,
    IndexCalculateRequest,
    IndexFactorCreate,
    IndexFactorResponse,
    IndexFactorUpdate,
    IndexFactorsGrouped,
)
from app.services.index import IndexService

router = APIRouter(prefix="/indexes", tags=["Indexes"])


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@router.get("/ranking", response_model=PaginatedResponse[FundListItem])
async def get_ranking(
    category_id: UUID | None = Query(None, description="Kategoriya filtri"),
    region_id: UUID | None = Query(None, description="Viloyat filtri"),
    grade: IndexGrade | None = Query(None, description="Daraja filtri"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Umumiy reyting ro'yxati — fondlar overall_score bo'yicha kamayish tartibida.
    Faqat aktiv va indeksi hisoblangan fondlar ko'rsatiladi.
    """
    service = IndexService(db)
    funds, meta = await service.get_ranking(
        page=page,
        per_page=per_page,
        category_id=category_id,
        region_id=region_id,
        grade=grade.value if grade else None,
    )
    return PaginatedResponse(
        data=[FundListItem.model_validate(f) for f in funds],
        meta=meta,
    )


@router.get("/factors", response_model=DataResponse[IndexFactorsGrouped])
async def get_factors(db: AsyncSession = Depends(get_db)):
    """
    Barcha aktiv indeks omillari — transparency, openness, trust bo'yicha guruhlanib.
    """
    service = IndexService(db)
    grouped = await service.get_factors_grouped()
    return DataResponse(data=grouped)


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{fund_id}/scores",
    response_model=DataResponse[FundIndexCalcResponse],
)
async def get_fund_scores(
    fund_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fond uchun joriy omil ballarini qaytarish (public)."""
    service = IndexService(db)
    repo = service.idx_repo
    all_factors = await repo.get_active_factors()
    all_stored = await repo.get_fund_scores(fund_id)
    score_map = {s.factor_id: s.score for s in all_stored}
    note_map = {s.factor_id: s.note for s in all_stored}
    fund_index = await repo.get_fund_index(fund_id)

    from decimal import Decimal
    factor_scores = [
        FundIndexScoreItem(
            factor_id=factor.id,
            index_type=factor.index_type,
            factor_name_uz=factor.name_uz,
            weight=factor.weight,
            score=score_map.get(factor.id, Decimal("0")),
            note=note_map.get(factor.id),
        )
        for factor in all_factors
    ]
    return DataResponse(
        data=FundIndexCalcResponse(
            fund_id=fund_id,
            transparency_score=fund_index.transparency_score if fund_index else Decimal("0"),
            openness_score=fund_index.openness_score if fund_index else Decimal("0"),
            trust_score=fund_index.trust_score if fund_index else Decimal("0"),
            overall_score=fund_index.overall_score if fund_index else Decimal("0"),
            grade=fund_index.grade if fund_index else IndexGrade.unrated,
            calculated_at=fund_index.calculated_at if fund_index else None,
            factor_scores=factor_scores,
        )
    )


@router.post(
    "/{fund_id}/calculate",
    status_code=status.HTTP_200_OK,
    response_model=DataResponse[FundIndexCalcResponse],
)
async def calculate_index(
    fund_id: UUID,
    data: IndexCalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Fond indeksini hisoblash (TZ 2.4):

        Umumiy = (Shaffoflik × 40%) + (Ochiqlik × 30%) + (Ishonchlilik × 30%)

    So'rovda har bir omil uchun ball (0–100) yuboriladi.
    Yuborilmagan omillar eski ball bilan (yoki 0) qoladi.
    """
    service = IndexService(db)
    result = await service.calculate(fund_id=fund_id, data=data)
    return DataResponse(
        message="Indeks muvaffaqiyatli hisoblandi",
        data=result,
    )


@router.post(
    "/factors",
    response_model=DataResponse[IndexFactorResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_factor(
    data: IndexFactorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """Yangi indeks omilini qo'shish."""
    from app.models.index import IndexFactor
    factor = IndexFactor(
        index_type=data.index_type,
        name_uz=data.name_uz,
        name_ru=data.name_ru,
        name_en=data.name_en,
        weight=data.weight,
        order=data.order,
        is_active=True,
    )
    db.add(factor)
    await db.flush()
    await db.refresh(factor)
    return DataResponse(
        message="Omil qo'shildi",
        data=IndexFactorResponse.model_validate(factor),
    )


@router.delete(
    "/factors/{factor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_factor(
    factor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """Indeks omilini o'chirish."""
    from sqlalchemy import delete as sa_delete
    from app.models.index import IndexFactor
    await db.execute(sa_delete(IndexFactor).where(IndexFactor.id == factor_id))


@router.put(
    "/factors/{factor_id}",
    response_model=DataResponse[IndexFactorResponse],
)
async def update_factor(
    factor_id: UUID,
    data: IndexFactorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Indeks omilini yangilash — og'irlik (weight), nom, tartib raqami yoki
    faol/nofaol holatini o'zgartirish.
    """
    service = IndexService(db)
    factor = await service.update_factor(factor_id, data)
    return DataResponse(
        message="Omil muvaffaqiyatli yangilandi",
        data=IndexFactorResponse.model_validate(factor),
    )
