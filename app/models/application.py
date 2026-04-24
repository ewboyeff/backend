from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Application(Base):
    __tablename__ = "applications"

    type: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)
