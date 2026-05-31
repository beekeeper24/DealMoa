from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.db.session import get_session
from app.modules.auth.router import bearer_scheme, get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser, AuthUseCases
from app.modules.events.repository import DomainEventsRepository
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.evidence.repository import EvidenceRepository
from app.modules.evidence.schemas import (
    PriceHistoryListResponse,
    PriceHistorySnapshotResponse,
    PublicVerifiedReviewListResponse,
    PublicVerifiedReviewResponse,
    ReviewStatus,
    VerifiedReviewCreateRequest,
    VerifiedReviewListResponse,
    VerifiedReviewResponse,
    VerifiedReviewReviewRequest,
)
from app.modules.evidence.use_cases import EvidenceUseCases
from app.modules.products.repository import ProductRepository

router = APIRouter(prefix="/products", tags=["evidence"])
admin_router = APIRouter(prefix="/admin/verified-reviews", tags=["admin-verified-reviews"])


def get_evidence_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> EvidenceUseCases:
    return EvidenceUseCases(
        evidence_repository=EvidenceRepository(session),
        product_repository=ProductRepository(session),
        domain_events=DomainEventsUseCases(repository=DomainEventsRepository(session)),
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthenticatedUser:
    if credentials is None:
        raise UnauthorizedException()
    return auth_use_cases.get_current_user(credentials.credentials)


@router.get("/{product_id}/price-history", response_model=PriceHistoryListResponse)
def list_price_history(
    product_id: str,
    use_cases: Annotated[EvidenceUseCases, Depends(get_evidence_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> PriceHistoryListResponse:
    page = use_cases.list_price_history(product_id=product_id, limit=limit, cursor=cursor)
    return PriceHistoryListResponse(
        items=[PriceHistorySnapshotResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@router.post(
    "/{product_id}/verified-reviews",
    response_model=VerifiedReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_verified_review(
    product_id: str,
    request: VerifiedReviewCreateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[EvidenceUseCases, Depends(get_evidence_use_cases)],
) -> VerifiedReviewResponse:
    return VerifiedReviewResponse.model_validate(
        use_cases.create_verified_review(
            actor=current_user,
            product_id=product_id,
            request=request,
        )
    )


@router.get("/{product_id}/verified-reviews", response_model=PublicVerifiedReviewListResponse)
def list_product_verified_reviews(
    product_id: str,
    use_cases: Annotated[EvidenceUseCases, Depends(get_evidence_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> PublicVerifiedReviewListResponse:
    page = use_cases.list_product_verified_reviews(
        product_id=product_id,
        limit=limit,
        cursor=cursor,
    )
    return PublicVerifiedReviewListResponse(
        items=[PublicVerifiedReviewResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@admin_router.get("", response_model=VerifiedReviewListResponse)
def list_admin_verified_reviews(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[EvidenceUseCases, Depends(get_evidence_use_cases)],
    review_status: Annotated[ReviewStatus, Query(alias="status")] = "pending_review",
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> VerifiedReviewListResponse:
    page = use_cases.list_admin_verified_reviews(
        actor=current_user,
        status=review_status,
        limit=limit,
        cursor=cursor,
    )
    return VerifiedReviewListResponse(
        items=[VerifiedReviewResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@admin_router.patch("/{review_id}", response_model=VerifiedReviewResponse)
def review_verified_review(
    review_id: str,
    request: VerifiedReviewReviewRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[EvidenceUseCases, Depends(get_evidence_use_cases)],
) -> VerifiedReviewResponse:
    return VerifiedReviewResponse.model_validate(
        use_cases.review_verified_review(
            actor=current_user,
            review_id=review_id,
            request=request,
        )
    )
