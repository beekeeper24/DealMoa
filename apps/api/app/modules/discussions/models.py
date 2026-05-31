from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.auth.models import User
from app.modules.products.models import Product


def new_uuid() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductDiscussionComment(TimestampMixin, Base):
    __tablename__ = "product_discussion_comments"
    __table_args__ = (
        Index(
            "ix_product_discussion_comments_product_status_created_at",
            "product_id",
            "status",
            "created_at",
        ),
        Index("ix_product_discussion_comments_status_created_at", "status", "created_at"),
        Index("ix_product_discussion_comments_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    moderated_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    moderation_note: Mapped[str | None] = mapped_column(Text)
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped[Product] = relationship()
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    moderator: Mapped[User | None] = relationship(foreign_keys=[moderated_by_user_id])
