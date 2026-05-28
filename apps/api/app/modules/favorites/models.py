from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.auth.models import User
from app.modules.products.models import Auction, Deal, Product


def new_uuid() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductFavorite(TimestampMixin, Base):
    __tablename__ = "product_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_product_favorites_user_product"),
        Index("ix_product_favorites_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False)

    user: Mapped[User] = relationship()
    product: Mapped[Product] = relationship()


class DealFavorite(TimestampMixin, Base):
    __tablename__ = "deal_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "deal_id", name="uq_deal_favorites_user_deal"),
        Index("ix_deal_favorites_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    deal_id: Mapped[str] = mapped_column(ForeignKey("deals.id"), nullable=False)

    user: Mapped[User] = relationship()
    deal: Mapped[Deal] = relationship()


class AuctionFavorite(TimestampMixin, Base):
    __tablename__ = "auction_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "auction_id", name="uq_auction_favorites_user_auction"),
        Index("ix_auction_favorites_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    auction_id: Mapped[str] = mapped_column(ForeignKey("auctions.id"), nullable=False)

    user: Mapped[User] = relationship()
    auction: Mapped[Auction] = relationship()
