from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.auth.models import User
from app.modules.products.models import Product


def new_uuid() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PriceHistorySnapshot(TimestampMixin, Base):
    __tablename__ = "price_history_snapshots"
    __table_args__ = (
        Index("ix_price_history_product_observed_at", "product_id", "observed_at"),
        Index("ix_price_history_source", "source_type", "source_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="KRW")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    product: Mapped[Product] = relationship()


class VerifiedReview(TimestampMixin, Base):
    __tablename__ = "verified_reviews"
    __table_args__ = (
        Index(
            "ix_verified_reviews_product_status_created_at",
            "product_id",
            "status",
            "created_at",
        ),
        Index("ix_verified_reviews_status_created_at", "status", "created_at"),
        Index(
            "ix_verified_reviews_status_risk_created_at",
            "status",
            "moderation_risk_score",
            "created_at",
        ),
        Index("ix_verified_reviews_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    proof_type: Mapped[str] = mapped_column(String(80), nullable=False)
    proof_reference: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    ai_decision: Mapped[str | None] = mapped_column(String(80))
    ai_reason: Mapped[str | None] = mapped_column(Text)
    ai_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    moderation_risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    moderation_risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    moderation_risk_reasons_json: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    reviewed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped[Product] = relationship()
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    reviewer: Mapped[User | None] = relationship(foreign_keys=[reviewed_by_user_id])
