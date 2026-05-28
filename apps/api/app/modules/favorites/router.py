from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.db.session import get_session
from app.modules.auth.router import bearer_scheme, get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser, AuthUseCases
from app.modules.favorites.repository import FavoritesRepository
from app.modules.favorites.schemas import (
    AuctionFavoriteListResponse,
    AuctionFavoriteResponse,
    DealFavoriteListResponse,
    DealFavoriteResponse,
    ProductFavoriteListResponse,
    ProductFavoriteResponse,
)
from app.modules.favorites.use_cases import FavoritesUseCases

router = APIRouter(prefix="/me/favorites", tags=["favorites"])


def get_favorites_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> FavoritesUseCases:
    return FavoritesUseCases(repository=FavoritesRepository(session))


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthenticatedUser:
    if credentials is None:
        raise UnauthorizedException()
    return auth_use_cases.get_current_user(credentials.credentials)


@router.put("/products/{product_id}", response_model=ProductFavoriteResponse)
def add_product_favorite(
    product_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[FavoritesUseCases, Depends(get_favorites_use_cases)],
) -> ProductFavoriteResponse:
    favorite = use_cases.add_product_favorite(user_id=current_user.id, product_id=product_id)
    return ProductFavoriteResponse.model_validate(favorite)


@router.delete("/products/{product_id}", status_code=204)
def remove_product_favorite(
    product_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[FavoritesUseCases, Depends(get_favorites_use_cases)],
) -> Response:
    use_cases.remove_product_favorite(user_id=current_user.id, product_id=product_id)
    return Response(status_code=204)


@router.get("/products", response_model=ProductFavoriteListResponse)
def list_product_favorites(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[FavoritesUseCases, Depends(get_favorites_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> ProductFavoriteListResponse:
    page = use_cases.list_product_favorites(
        user_id=current_user.id,
        limit=limit,
        cursor=cursor,
    )
    return ProductFavoriteListResponse(
        items=[ProductFavoriteResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@router.put("/deals/{deal_id}", response_model=DealFavoriteResponse)
def add_deal_favorite(
    deal_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[FavoritesUseCases, Depends(get_favorites_use_cases)],
) -> DealFavoriteResponse:
    favorite = use_cases.add_deal_favorite(user_id=current_user.id, deal_id=deal_id)
    return DealFavoriteResponse.model_validate(favorite)


@router.delete("/deals/{deal_id}", status_code=204)
def remove_deal_favorite(
    deal_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[FavoritesUseCases, Depends(get_favorites_use_cases)],
) -> Response:
    use_cases.remove_deal_favorite(user_id=current_user.id, deal_id=deal_id)
    return Response(status_code=204)


@router.get("/deals", response_model=DealFavoriteListResponse)
def list_deal_favorites(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[FavoritesUseCases, Depends(get_favorites_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> DealFavoriteListResponse:
    page = use_cases.list_deal_favorites(user_id=current_user.id, limit=limit, cursor=cursor)
    return DealFavoriteListResponse(
        items=[DealFavoriteResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@router.put("/auctions/{auction_id}", response_model=AuctionFavoriteResponse)
def add_auction_favorite(
    auction_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[FavoritesUseCases, Depends(get_favorites_use_cases)],
) -> AuctionFavoriteResponse:
    favorite = use_cases.add_auction_favorite(user_id=current_user.id, auction_id=auction_id)
    return AuctionFavoriteResponse.model_validate(favorite)


@router.delete("/auctions/{auction_id}", status_code=204)
def remove_auction_favorite(
    auction_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[FavoritesUseCases, Depends(get_favorites_use_cases)],
) -> Response:
    use_cases.remove_auction_favorite(user_id=current_user.id, auction_id=auction_id)
    return Response(status_code=204)


@router.get("/auctions", response_model=AuctionFavoriteListResponse)
def list_auction_favorites(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[FavoritesUseCases, Depends(get_favorites_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> AuctionFavoriteListResponse:
    page = use_cases.list_auction_favorites(
        user_id=current_user.id,
        limit=limit,
        cursor=cursor,
    )
    return AuctionFavoriteListResponse(
        items=[AuctionFavoriteResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )
