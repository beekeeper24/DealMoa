from datetime import UTC, datetime
from typing import Any

from app.core.pagination import CursorPage
from app.db.base import Base
from app.modules.demo_seed.cli import run_demo_seed
from app.modules.demo_seed.use_cases import seed_korean_demo_data
from app.modules.favorites.models import AuctionFavorite, DealFavorite
from app.modules.products.models import Auction, AuctionBid, Deal, Product
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def make_session() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_seed_korean_demo_data_creates_searchable_products_deals_and_auctions() -> None:
    session_factory = make_session()
    session = session_factory()
    try:
        summary = seed_korean_demo_data(
            session,
            now=lambda: datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
        )
        session.commit()

        products = list(session.scalars(select(Product).order_by(Product.name)))
        deals = list(session.scalars(select(Deal).order_by(Deal.title)))
        auctions = list(session.scalars(select(Auction).order_by(Auction.title)))
        bids = list(session.scalars(select(AuctionBid)))
        deal_favorites = list(session.scalars(select(DealFavorite)))
        auction_favorites = list(session.scalars(select(AuctionFavorite)))
    finally:
        session.close()

    assert summary.products_created == 6
    assert summary.deals_created == 6
    assert summary.auctions_created == 6
    assert {product.name for product in products} >= {
        "삼성 갤럭시 S26 256GB",
        "LG 스탠바이미 고 27인치",
        "다이슨 슈퍼소닉 뉴럴 헤어드라이어",
    }
    assert products[0].category in {"생활가전", "스마트폰", "노트북", "음향기기"}
    assert any("한국어 검색" in str(product.specs) for product in products)
    assert any("핫딜" in deal.title or "특가" in deal.title for deal in deals)
    assert any("경매" in auction.title or "미개봉" in auction.title for auction in auctions)
    assert len(bids) >= 6
    assert len(deal_favorites) >= 6
    assert len(auction_favorites) >= 6


def test_seed_korean_demo_data_is_idempotent() -> None:
    session_factory = make_session()
    session = session_factory()
    try:
        first = seed_korean_demo_data(
            session,
            now=lambda: datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
        )
        session.commit()

        second = seed_korean_demo_data(
            session,
            now=lambda: datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
        )
        session.commit()

        product_count = len(list(session.scalars(select(Product))))
        deal_count = len(list(session.scalars(select(Deal))))
        auction_count = len(list(session.scalars(select(Auction))))
        bid_count = len(list(session.scalars(select(AuctionBid))))
    finally:
        session.close()

    assert first.products_created == 6
    assert second.products_created == 0
    assert second.products_reused == 6
    assert second.deals_created == 0
    assert second.auctions_created == 0
    assert second.auction_bids_created == 0
    assert product_count == 6
    assert deal_count == 6
    assert auction_count == 6
    assert bid_count >= 6


class FakeSearchClient:
    def __init__(self) -> None:
        self.recreated = False
        self.replaced: list[tuple[str, list[dict[str, Any]]]] = []

    def recreate_indexes(self) -> None:
        self.recreated = True

    def replace_documents(self, kind: str, documents: list[dict[str, Any]]) -> None:
        self.replaced.append((kind, documents))

    def index_document(self, kind: str, document: dict[str, Any]) -> None:
        raise AssertionError("demo seed reindex test should not index a single document")

    def search(
        self,
        kind: str,
        *,
        query: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        raise AssertionError("demo seed reindex test should not call search")

    def rank_auctions(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        raise AssertionError("demo seed reindex test should not call auction ranking")

    def rank_deals(
        self,
        *,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, Any]]:
        raise AssertionError("demo seed reindex test should not call deal ranking")


def test_run_demo_seed_can_reindex_seeded_korean_documents() -> None:
    session_factory = make_session()
    search_client = FakeSearchClient()

    result = run_demo_seed(
        session_factory=session_factory,
        reindex=True,
        search_client=search_client,
        now=lambda: datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
    )

    assert result["seed"]["products_created"] == 6
    assert result["reindex"] == {"products": 6, "deals": 6, "auctions": 6}
    assert search_client.recreated is True
    assert [kind for kind, _documents in search_client.replaced] == [
        "products",
        "deals",
        "auctions",
    ]
    assert any(
        document["name"] == "삼성 갤럭시 S26 256GB"
        for kind, documents in search_client.replaced
        if kind == "products"
        for document in documents
    )


def test_run_demo_seed_skips_reindex_by_default() -> None:
    session_factory = make_session()
    search_client = FakeSearchClient()

    result = run_demo_seed(
        session_factory=session_factory,
        reindex=False,
        search_client=search_client,
        now=lambda: datetime(2026, 6, 5, 12, 0, tzinfo=UTC),
    )

    assert result["seed"]["products_created"] == 6
    assert result["reindex"] is None
    assert search_client.recreated is False
