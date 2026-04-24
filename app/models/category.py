from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.fund import Fund


class Category(Base):
    __tablename__ = "categories"

    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    funds: Mapped[list[Fund]] = relationship(
        back_populates="category",
        lazy="selectin",
    )

