from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def new_uuid() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_name", "name"),
        Index("ix_products_brand", "brand"),
        Index("ix_products_model_name", "model_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(120))
    model_name: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str | None] = mapped_column(String(120))
    specs: Mapped[dict[str, object] | None] = mapped_column(JSON)

    deals: Mapped[list["Deal"]] = relationship(back_populates="product")
    auctions: Mapped[list["Auction"]] = relationship(back_populates="product")


class Deal(TimestampMixin, Base):
    __tablename__ = "deals"
    __table_args__ = (
        Index("ix_deals_product_id", "product_id"),
        Index("ix_deals_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    seller: Mapped[str | None] = mapped_column(String(120))
    original_price: Mapped[int | None] = mapped_column(Integer)
    sale_price: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="KRW")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped[Product] = relationship(back_populates="deals")


class Auction(TimestampMixin, Base):
    __tablename__ = "auctions"
    __table_args__ = (
        Index("ix_auctions_product_id", "product_id"),
        Index("ix_auctions_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    seller: Mapped[str | None] = mapped_column(String(120))
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)
    bid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="KRW")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    product: Mapped[Product] = relationship(back_populates="auctions")
    bids: Mapped[list["AuctionBid"]] = relationship(back_populates="auction")
    views: Mapped[list["AuctionView"]] = relationship(back_populates="auction")


class AuctionBid(TimestampMixin, Base):
    __tablename__ = "auction_bids"
    __table_args__ = (
        Index("ix_auction_bids_auction_id", "auction_id"),
        Index("ix_auction_bids_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    auction_id: Mapped[str] = mapped_column(ForeignKey("auctions.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    auction: Mapped[Auction] = relationship(back_populates="bids")


class AuctionView(TimestampMixin, Base):
    __tablename__ = "auction_views"
    __table_args__ = (
        Index("ix_auction_views_auction_id_created_at", "auction_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    auction_id: Mapped[str] = mapped_column(ForeignKey("auctions.id"), nullable=False)

    auction: Mapped[Auction] = relationship(back_populates="views")
