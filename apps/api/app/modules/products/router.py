from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import (
    AuctionCreateRequest,
    AuctionListResponse,
    AuctionResponse,
    DealCreateRequest,
    DealListResponse,
    DealResponse,
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
)
from app.modules.products.use_cases import ProductUseCases

router = APIRouter(prefix="/products", tags=["products"])
offer_router = APIRouter(tags=["offers"])


def get_product_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> ProductUseCases:
    return ProductUseCases(ProductRepository(session))


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    request: ProductCreateRequest,
    use_cases: Annotated[ProductUseCases, Depends(get_product_use_cases)],
) -> ProductResponse:
    return ProductResponse.model_validate(use_cases.create_product(request))


@router.get("", response_model=ProductListResponse)
def list_products(
    use_cases: Annotated[ProductUseCases, Depends(get_product_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> ProductListResponse:
    page = use_cases.list_products(limit=limit, cursor=cursor)
    return ProductListResponse(
        items=[ProductResponse.model_validate(product) for product in page.items],
        nextCursor=page.next_cursor,
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    use_cases: Annotated[ProductUseCases, Depends(get_product_use_cases)],
) -> ProductResponse:
    return ProductResponse.model_validate(use_cases.get_product(product_id))


@router.post(
    "/{product_id}/deals",
    response_model=DealResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deal(
    product_id: str,
    request: DealCreateRequest,
    use_cases: Annotated[ProductUseCases, Depends(get_product_use_cases)],
) -> DealResponse:
    return DealResponse.model_validate(use_cases.create_deal(product_id, request))


@router.get("/{product_id}/deals", response_model=DealListResponse)
def list_product_deals(
    product_id: str,
    use_cases: Annotated[ProductUseCases, Depends(get_product_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> DealListResponse:
    page = use_cases.list_deals_for_product(product_id, limit=limit, cursor=cursor)
    return DealListResponse(
        items=[DealResponse.model_validate(deal) for deal in page.items],
        nextCursor=page.next_cursor,
    )


@router.post(
    "/{product_id}/auctions",
    response_model=AuctionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_auction(
    product_id: str,
    request: AuctionCreateRequest,
    use_cases: Annotated[ProductUseCases, Depends(get_product_use_cases)],
) -> AuctionResponse:
    return AuctionResponse.model_validate(use_cases.create_auction(product_id, request))


@router.get("/{product_id}/auctions", response_model=AuctionListResponse)
def list_product_auctions(
    product_id: str,
    use_cases: Annotated[ProductUseCases, Depends(get_product_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> AuctionListResponse:
    page = use_cases.list_auctions_for_product(product_id, limit=limit, cursor=cursor)
    return AuctionListResponse(
        items=[AuctionResponse.model_validate(auction) for auction in page.items],
        nextCursor=page.next_cursor,
    )


@offer_router.get("/deals/{deal_id}", response_model=DealResponse)
def get_deal(
    deal_id: str,
    use_cases: Annotated[ProductUseCases, Depends(get_product_use_cases)],
) -> DealResponse:
    return DealResponse.model_validate(use_cases.get_deal(deal_id))


@offer_router.get("/auctions/{auction_id}", response_model=AuctionResponse)
def get_auction(
    auction_id: str,
    use_cases: Annotated[ProductUseCases, Depends(get_product_use_cases)],
) -> AuctionResponse:
    return AuctionResponse.model_validate(use_cases.get_auction(auction_id))
