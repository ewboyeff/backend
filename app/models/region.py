from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.fund import Fund
    from app.models.project import Project


class Region(Base):
    __tablename__ = "regions"

    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    funds: Mapped[list[Fund]] = relationship(
        back_populates="region",
        lazy="selectin",
    )
    projects: Mapped[list[Project]] = relationship(
        back_populates="region",
        lazy="selectin",
    )

