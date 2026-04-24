from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User, UserRole
from app.schemas.base import DataResponse, PaginatedResponse
from app.schemas.news import NewsCreate, NewsResponse, NewsUpdate
from app.services.news import NewsService

router = APIRouter(prefix="/news", tags=["News"])


@router.get("", response_model=PaginatedResponse[NewsResponse])
async def list_news(
    is_featured: bool | None = Query(None, description="Featured filter"),
    fund_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Yangiliklar ro'yxati (faqat aktiv).
    """
    service = NewsService(db)
    news_list, meta = await service.get_list(
        page=page,
        per_page=per_page,
        is_featured=is_featured,
        fund_id=fund_id,
        only_active=True,
    )
    return PaginatedResponse(
        data=[NewsResponse.model_validate(n) for n in news_list],
        meta=meta,
    )


@router.get("/{news_id}", response_model=DataResponse[NewsResponse])
async def get_news(
    news_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Bitta yangilik (faqat ID bo'yicha).
    """
    service = NewsService(db)
    news = await service.get_by_id(news_id)
    return DataResponse(data=NewsResponse.model_validate(news))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DataResponse[NewsResponse],
)
async def create_news(
    data: NewsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Yangilik qo'shish (faqat admin).
    """
    service = NewsService(db)
    news = await service.create(data)
    return DataResponse(
        message="Yangilik muvaffaqiyatli qo'shildi",
        data=NewsResponse.model_validate(news),
    )


@router.put("/{news_id}", response_model=DataResponse[NewsResponse])
async def update_news(
    news_id: UUID,
    data: NewsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Yangilikni yangilash (faqat admin).
    """
    service = NewsService(db)
    news = await service.update(news_id, data)
    return DataResponse(
        message="Yangilik muvaffaqiyatli yangilandi",
        data=NewsResponse.model_validate(news),
    )


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    news_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    """
    Yangilikni o'chirish (faqat admin).
    """
    service = NewsService(db)
    await service.delete(news_id)
