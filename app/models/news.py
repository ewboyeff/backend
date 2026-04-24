from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.fund import Fund


class News(Base):
    __tablename__ = "news"

    fund_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("funds.id", ondelete="SET NULL"),
        nullable=True,
    )
    title_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gradient: Mapped[str | None] = mapped_column(String(100), nullable=True)
    read_time: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    fund: Mapped[Fund | None] = relationship(
        back_populates="news_items",
        lazy="selectin",
    )

