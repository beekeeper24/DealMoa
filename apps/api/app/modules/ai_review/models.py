from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.modules.products.models import TimestampMixin, new_uuid


class AIReviewUsageEvent(TimestampMixin, Base):
    __tablename__ = "ai_review_usage_events"
    __table_args__ = (
        Index("ix_ai_review_usage_events_user_id_created_at", "user_id", "created_at"),
        Index(
            "ix_ai_review_usage_events_user_target_created_at",
            "user_id",
            "target_type",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
