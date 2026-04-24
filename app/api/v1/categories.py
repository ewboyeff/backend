from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User, UserRole
from app.schemas.base import DataResponse
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate, RegionResponse
from app.services.category import CategoryService, RegionService

router = APIRouter(tags=["Categories & Regions"])


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@router.get("/categories", response_model=DataResponse[list[CategoryResponse]])
async def list_categories(
    db: AsyncSession = Depends(get_db),
):
    """
    Barcha aktiv kategoriyalar.
    """
    service = CategoryService(db)
    categories = await service.get_all(only_active=True)
    return DataResponse(data=[CategoryResponse.model_validate(c) for c in categories])


@router.post(
    "/categories",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[CategoryResponse],
)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Kategoriya qo'shish (faqat admin).
    """
    service = CategoryService(db)
    category = await service.create(data)
    return DataResponse(
        message="Kategoriya muvaffaqiyatli qo'shildi",
        data=CategoryResponse.model_validate(category),
    )


@router.put(
    "/categories/{category_id}",
    response_model=DataResponse[CategoryResponse],
)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Kategoriyani yangilash (faqat admin).
    """
    service = CategoryService(db)
    category = await service.update(category_id, data)
    return DataResponse(
        message="Kategoriya muvaffaqiyatli yangilandi",
        data=CategoryResponse.model_validate(category),
    )


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Kategoriyani o'chirish (faqat admin).
    """
    service = CategoryService(db)
    await service.delete(category_id)


# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------

@router.get("/regions", response_model=DataResponse[list[RegionResponse]])
async def list_regions(
    db: AsyncSession = Depends(get_db),
):
    """
    Barcha viloyatlar ro'yxati.
    """
    service = RegionService(db)
    regions = await service.get_all()
    return DataResponse(data=[RegionResponse.model_validate(r) for r in regions])
