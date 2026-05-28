from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session
from app.modules.products.repository import ProductRepository
from app.modules.search.client import ElasticsearchSearchClient
from app.modules.search.schemas import (
    AuctionSearchItem,
    AuctionSearchResponse,
    DealSearchItem,
    DealSearchResponse,
    ProductSearchItem,
    ProductSearchResponse,
    SearchReindexResponse,
)
from app.modules.search.use_cases import SearchUseCases

router = APIRouter(prefix="/search", tags=["search"])
admin_router = APIRouter(prefix="/admin/search", tags=["admin-search"])


def get_search_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> SearchUseCases:
    settings = get_settings()
    return SearchUseCases(
        ProductRepository(session),
        ElasticsearchSearchClient(settings.elasticsearch_url),
    )


@router.get("/products", response_model=ProductSearchResponse)
def search_products(
    use_cases: Annotated[SearchUseCases, Depends(get_search_use_cases)],
    q: Annotated[str, Query(min_length=1, max_length=120)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> ProductSearchResponse:
    page = use_cases.search_products(query=q, limit=limit, cursor=cursor)
    return ProductSearchResponse(
        items=[ProductSearchItem.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@router.get("/deals", response_model=DealSearchResponse)
def search_deals(
    use_cases: Annotated[SearchUseCases, Depends(get_search_use_cases)],
    q: Annotated[str, Query(min_length=1, max_length=120)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> DealSearchResponse:
    page = use_cases.search_deals(query=q, limit=limit, cursor=cursor)
    return DealSearchResponse(
        items=[DealSearchItem.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@router.get("/auctions/activity", response_model=AuctionSearchResponse)
def rank_auctions_by_activity(
    use_cases: Annotated[SearchUseCases, Depends(get_search_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> AuctionSearchResponse:
    page = use_cases.rank_auctions(limit=limit, cursor=cursor)
    return AuctionSearchResponse(
        items=[AuctionSearchItem.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@router.get("/auctions", response_model=AuctionSearchResponse)
def search_auctions(
    use_cases: Annotated[SearchUseCases, Depends(get_search_use_cases)],
    q: Annotated[str, Query(min_length=1, max_length=120)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> AuctionSearchResponse:
    page = use_cases.search_auctions(query=q, limit=limit, cursor=cursor)
    return AuctionSearchResponse(
        items=[AuctionSearchItem.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@admin_router.post("/reindex", response_model=SearchReindexResponse)
def rebuild_search_indexes(
    use_cases: Annotated[SearchUseCases, Depends(get_search_use_cases)],
) -> SearchReindexResponse:
    summary = use_cases.rebuild_indexes()
    return SearchReindexResponse(**summary)
