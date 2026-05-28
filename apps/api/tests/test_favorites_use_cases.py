from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.core.exceptions import (
    AuctionNotFoundException,
    DealNotFoundException,
    ProductNotFoundException,
)
from app.db.base import Base
from app.modules.auth.models import User
from app.modules.favorites.models import ProductFavorite
from app.modules.favorites.repository import FavoritesRepository
from app.modules.favorites.use_cases import FavoritesUseCases
from app.modules.products.models import Auction, Deal, Product
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

NOW = datetime(2026, 5, 28, tzinfo=UTC)


def make_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def add_user(session: Session, user_id: str = "user-1") -> User:
    user = User(
        id=user_id,
        email=f"{user_id}@example.com",
        nickname=user_id,
        role="USER",
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(user)
    return user


def add_product(session: Session, product_id: str, name: str = "테스트 상품") -> Product:
    product = Product(
        id=product_id,
        name=name,
        brand="DealMoa",
        model_name=None,
        category="electronics",
        specs=None,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(product)
    return product


def add_deal(session: Session, deal_id: str, product_id: str) -> Deal:
    deal = Deal(
        id=deal_id,
        product_id=product_id,
        title="특가 딜",
        source_url="https://example.com/deals/1",
        seller="Example",
        original_price=None,
        sale_price=10000,
        currency="KRW",
        status="active",
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(deal)
    return deal


def add_auction(session: Session, auction_id: str, product_id: str) -> Auction:
    auction = Auction(
        id=auction_id,
        product_id=product_id,
        title="경매 상품",
        source_url="https://example.com/auctions/1",
        seller="Example",
        current_price=10000,
        bid_count=3,
        currency="KRW",
        status="active",
        created_at=NOW,
        updated_at=NOW,
    )
    session.add(auction)
    return auction


def make_use_cases(session: Session) -> FavoritesUseCases:
    return FavoritesUseCases(repository=FavoritesRepository(session), now=lambda: NOW)


def test_add_product_favorite_is_idempotent_per_user() -> None:
    session = next(make_session())
    add_user(session)
    add_product(session, "product-1")
    use_cases = make_use_cases(session)

    first = use_cases.add_product_favorite(user_id="user-1", product_id="product-1")
    second = use_cases.add_product_favorite(user_id="user-1", product_id="product-1")
    session.commit()

    favorites = list(session.scalars(select(ProductFavorite)))
    assert first.id == second.id
    assert len(favorites) == 1
    assert favorites[0].user_id == "user-1"
    assert favorites[0].product_id == "product-1"


def test_add_product_favorite_rejects_missing_product() -> None:
    session = next(make_session())
    add_user(session)
    use_cases = make_use_cases(session)

    with pytest.raises(ProductNotFoundException) as exc_info:
        use_cases.add_product_favorite(user_id="user-1", product_id="missing-product")

    assert exc_info.value.error_code.code == "PRODUCT_NOT_FOUND"
    assert exc_info.value.details == {"productId": "missing-product"}


def test_remove_product_favorite_is_idempotent_but_validates_target() -> None:
    session = next(make_session())
    add_user(session)
    add_product(session, "product-1")
    use_cases = make_use_cases(session)
    use_cases.add_product_favorite(user_id="user-1", product_id="product-1")

    use_cases.remove_product_favorite(user_id="user-1", product_id="product-1")
    use_cases.remove_product_favorite(user_id="user-1", product_id="product-1")
    session.commit()

    assert list(session.scalars(select(ProductFavorite))) == []


def test_list_product_favorites_is_isolated_by_user_and_paginated() -> None:
    session = next(make_session())
    add_user(session, "user-1")
    add_user(session, "user-2")
    add_product(session, "product-1", "첫 상품")
    add_product(session, "product-2", "둘째 상품")
    use_cases = make_use_cases(session)
    first = use_cases.add_product_favorite(user_id="user-1", product_id="product-1")
    use_cases.add_product_favorite(user_id="user-1", product_id="product-2")
    use_cases.add_product_favorite(user_id="user-2", product_id="product-1")

    page = use_cases.list_product_favorites(user_id="user-1", limit=1, cursor=None)
    next_page = use_cases.list_product_favorites(
        user_id="user-1",
        limit=1,
        cursor=page.next_cursor,
    )

    assert len(page.items) == 1
    assert page.next_cursor is not None
    assert [favorite.user_id for favorite in page.items + next_page.items] == ["user-1", "user-1"]
    assert {favorite.product_id for favorite in page.items + next_page.items} == {
        "product-1",
        "product-2",
    }
    assert first.id in {favorite.id for favorite in page.items + next_page.items}


def test_deal_favorite_is_idempotent_and_validates_target() -> None:
    session = next(make_session())
    add_user(session)
    add_product(session, "product-1")
    add_deal(session, "deal-1", "product-1")
    use_cases = make_use_cases(session)

    first = use_cases.add_deal_favorite(user_id="user-1", deal_id="deal-1")
    second = use_cases.add_deal_favorite(user_id="user-1", deal_id="deal-1")
    use_cases.remove_deal_favorite(user_id="user-1", deal_id="deal-1")
    use_cases.remove_deal_favorite(user_id="user-1", deal_id="deal-1")

    assert first.id == second.id
    assert use_cases.list_deal_favorites(user_id="user-1", limit=20, cursor=None).items == []

    with pytest.raises(DealNotFoundException):
        use_cases.add_deal_favorite(user_id="user-1", deal_id="missing-deal")


def test_auction_favorite_is_idempotent_and_validates_target() -> None:
    session = next(make_session())
    add_user(session)
    add_product(session, "product-1")
    add_auction(session, "auction-1", "product-1")
    use_cases = make_use_cases(session)

    first = use_cases.add_auction_favorite(user_id="user-1", auction_id="auction-1")
    second = use_cases.add_auction_favorite(user_id="user-1", auction_id="auction-1")
    use_cases.remove_auction_favorite(user_id="user-1", auction_id="auction-1")
    use_cases.remove_auction_favorite(user_id="user-1", auction_id="auction-1")

    assert first.id == second.id
    assert use_cases.list_auction_favorites(user_id="user-1", limit=20, cursor=None).items == []

    with pytest.raises(AuctionNotFoundException):
        use_cases.add_auction_favorite(user_id="user-1", auction_id="missing-auction")
