from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.demo_seed.data import DEMO_USER_KEYS, KOREAN_DEMO_PRODUCTS, DemoProduct
from app.modules.favorites.models import AuctionFavorite, DealFavorite
from app.modules.products.models import Auction, AuctionBid, Deal, Product


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class DemoSeedSummary:
    users_created: int = 0
    users_reused: int = 0
    products_created: int = 0
    products_reused: int = 0
    deals_created: int = 0
    deals_reused: int = 0
    auctions_created: int = 0
    auctions_reused: int = 0
    auction_bids_created: int = 0
    auction_bids_reused: int = 0
    deal_favorites_created: int = 0
    deal_favorites_reused: int = 0
    auction_favorites_created: int = 0
    auction_favorites_reused: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def seed_korean_demo_data(
    session: Session,
    *,
    now: Callable[[], datetime] | None = None,
) -> DemoSeedSummary:
    timestamp = (now or utc_now)()
    summary = DemoSeedSummary()
    users = _ensure_demo_users(session, summary=summary, now=timestamp)

    for product_data in KOREAN_DEMO_PRODUCTS:
        product = _ensure_product(session, product_data, summary=summary, now=timestamp)
        deal = _ensure_deal(
            session,
            product=product,
            product_data=product_data,
            summary=summary,
            now=timestamp,
        )
        auction = _ensure_auction(
            session,
            product=product,
            product_data=product_data,
            summary=summary,
            now=timestamp,
        )
        _ensure_deal_favorites(
            session,
            deal=deal,
            user_ids=[users[key].id for key in product_data.deal.favorite_user_keys],
            summary=summary,
            now=timestamp,
        )
        _ensure_auction_bids(
            session,
            auction=auction,
            product_data=product_data,
            user_ids={key: users[key].id for key in DEMO_USER_KEYS},
            summary=summary,
            now=timestamp,
        )
        _ensure_auction_favorites(
            session,
            auction=auction,
            user_ids=[users[key].id for key in product_data.auction.favorite_user_keys],
            summary=summary,
            now=timestamp,
        )

    session.flush()
    return summary


def _ensure_demo_users(
    session: Session,
    *,
    summary: DemoSeedSummary,
    now: datetime,
) -> dict[str, User]:
    users: dict[str, User] = {}
    for index, user_key in enumerate(DEMO_USER_KEYS, start=1):
        user = session.get(User, user_key)
        if user is None:
            user = User(
                id=user_key,
                email=f"{user_key}@dealmoa.local",
                nickname=f"데모사용자{index}",
                role="USER",
                created_at=now,
                updated_at=now,
            )
            session.add(user)
            summary.users_created += 1
        else:
            user.email = f"{user_key}@dealmoa.local"
            user.nickname = f"데모사용자{index}"
            user.updated_at = now
            summary.users_reused += 1
        users[user_key] = user
    session.flush()
    return users


def _ensure_product(
    session: Session,
    product_data: DemoProduct,
    *,
    summary: DemoSeedSummary,
    now: datetime,
) -> Product:
    product = session.scalar(
        select(Product).where(Product.model_name == product_data.model_name).limit(1)
    )
    if product is None:
        product = Product(
            name=product_data.name,
            brand=product_data.brand,
            model_name=product_data.model_name,
            category=product_data.category,
            specs=product_data.specs,
            created_at=now,
            updated_at=now,
        )
        session.add(product)
        summary.products_created += 1
    else:
        product.name = product_data.name
        product.brand = product_data.brand
        product.category = product_data.category
        product.specs = product_data.specs
        product.updated_at = now
        summary.products_reused += 1
    session.flush()
    return product


def _ensure_deal(
    session: Session,
    *,
    product: Product,
    product_data: DemoProduct,
    summary: DemoSeedSummary,
    now: datetime,
) -> Deal:
    deal_data = product_data.deal
    deal = session.scalar(select(Deal).where(Deal.source_url == deal_data.source_url).limit(1))
    if deal is None:
        deal = Deal(
            product_id=product.id,
            title=deal_data.title,
            source_url=deal_data.source_url,
            seller=deal_data.seller,
            original_price=deal_data.original_price,
            sale_price=deal_data.sale_price,
            currency="KRW",
            status="active",
            started_at=now,
            ended_at=None,
            created_at=now,
            updated_at=now,
        )
        session.add(deal)
        summary.deals_created += 1
    else:
        deal.product_id = product.id
        deal.title = deal_data.title
        deal.seller = deal_data.seller
        deal.original_price = deal_data.original_price
        deal.sale_price = deal_data.sale_price
        deal.currency = "KRW"
        deal.status = "active"
        deal.started_at = deal.started_at or now
        deal.ended_at = None
        deal.updated_at = now
        summary.deals_reused += 1
    session.flush()
    return deal


def _ensure_auction(
    session: Session,
    *,
    product: Product,
    product_data: DemoProduct,
    summary: DemoSeedSummary,
    now: datetime,
) -> Auction:
    auction_data = product_data.auction
    auction = session.scalar(
        select(Auction).where(Auction.source_url == auction_data.source_url).limit(1)
    )
    if auction is None:
        auction = Auction(
            product_id=product.id,
            title=auction_data.title,
            source_url=auction_data.source_url,
            seller=auction_data.seller,
            current_price=auction_data.current_price,
            bid_count=auction_data.bid_count,
            currency="KRW",
            status="active",
            ends_at=None,
            created_at=now,
            updated_at=now,
        )
        session.add(auction)
        summary.auctions_created += 1
    else:
        auction.product_id = product.id
        auction.title = auction_data.title
        auction.seller = auction_data.seller
        auction.current_price = auction_data.current_price
        auction.bid_count = auction_data.bid_count
        auction.currency = "KRW"
        auction.status = "active"
        auction.ends_at = None
        auction.updated_at = now
        summary.auctions_reused += 1
    session.flush()
    return auction


def _ensure_deal_favorites(
    session: Session,
    *,
    deal: Deal,
    user_ids: list[str],
    summary: DemoSeedSummary,
    now: datetime,
) -> None:
    for user_id in user_ids:
        favorite = session.scalar(
            select(DealFavorite)
            .where(DealFavorite.user_id == user_id, DealFavorite.deal_id == deal.id)
            .limit(1)
        )
        if favorite is None:
            session.add(
                DealFavorite(
                    user_id=user_id,
                    deal_id=deal.id,
                    created_at=now,
                    updated_at=now,
                )
            )
            summary.deal_favorites_created += 1
        else:
            favorite.updated_at = now
            summary.deal_favorites_reused += 1


def _ensure_auction_bids(
    session: Session,
    *,
    auction: Auction,
    product_data: DemoProduct,
    user_ids: dict[str, str],
    summary: DemoSeedSummary,
    now: datetime,
) -> None:
    for bid_data in product_data.auction.bids:
        user_id = user_ids[bid_data.user_key]
        bid = session.scalar(
            select(AuctionBid)
            .where(
                AuctionBid.auction_id == auction.id,
                AuctionBid.user_id == user_id,
                AuctionBid.amount == bid_data.amount,
            )
            .limit(1)
        )
        if bid is None:
            session.add(
                AuctionBid(
                    auction_id=auction.id,
                    user_id=user_id,
                    amount=bid_data.amount,
                    created_at=now,
                    updated_at=now,
                )
            )
            summary.auction_bids_created += 1
        else:
            bid.updated_at = now
            summary.auction_bids_reused += 1


def _ensure_auction_favorites(
    session: Session,
    *,
    auction: Auction,
    user_ids: list[str],
    summary: DemoSeedSummary,
    now: datetime,
) -> None:
    for user_id in user_ids:
        favorite = session.scalar(
            select(AuctionFavorite)
            .where(
                AuctionFavorite.user_id == user_id,
                AuctionFavorite.auction_id == auction.id,
            )
            .limit(1)
        )
        if favorite is None:
            session.add(
                AuctionFavorite(
                    user_id=user_id,
                    auction_id=auction.id,
                    created_at=now,
                    updated_at=now,
                )
            )
            summary.auction_favorites_created += 1
        else:
            favorite.updated_at = now
            summary.auction_favorites_reused += 1
