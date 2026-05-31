from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.auth.models import User


def new_uuid() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Submission(TimestampMixin, Base):
    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_status_created_at", "status", "created_at"),
        Index("ix_submissions_user_id_created_at", "user_id", "created_at"),
        Index("ix_submissions_source_url", "source_url", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    offer_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(120))
    model_name: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str | None] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    seller: Mapped[str | None] = mapped_column(String(120))
    original_price: Mapped[int | None] = mapped_column(Integer)
    sale_price: Mapped[int | None] = mapped_column(Integer)
    current_price: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="KRW")
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    ai_decision: Mapped[str | None] = mapped_column(String(80))
    ai_reason: Mapped[str | None] = mapped_column(Text)
    ai_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_product_id: Mapped[str | None] = mapped_column(String(36))
    published_offer_type: Mapped[str | None] = mapped_column(String(30))
    published_offer_id: Mapped[str | None] = mapped_column(String(36))

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by_user_id])
