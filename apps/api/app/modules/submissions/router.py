from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.db.session import get_session
from app.modules.auth.router import bearer_scheme, get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser, AuthUseCases
from app.modules.events.repository import DomainEventsRepository
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.repository import ProductRepository
from app.modules.submissions.repository import SubmissionsRepository
from app.modules.submissions.schemas import (
    ProductMatchListResponse,
    ProductMatchResponse,
    SubmissionCreateRequest,
    SubmissionListResponse,
    SubmissionResponse,
    SubmissionReviewRequest,
    SubmissionStatus,
)
from app.modules.submissions.use_cases import ProductMatch, SubmissionsUseCases

router = APIRouter(prefix="/submissions", tags=["submissions"])
me_router = APIRouter(prefix="/me/submissions", tags=["submissions"])
admin_router = APIRouter(prefix="/admin/submissions", tags=["admin-submissions"])


def get_submissions_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> SubmissionsUseCases:
    return SubmissionsUseCases(
        submissions_repository=SubmissionsRepository(session),
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


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    request: SubmissionCreateRequest,
    response: Response,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[SubmissionsUseCases, Depends(get_submissions_use_cases)],
) -> SubmissionResponse:
    result = use_cases.create_submission(actor=current_user, request=request)
    if not result.created:
        response.status_code = status.HTTP_200_OK
    return SubmissionResponse.model_validate(result.submission)


@me_router.get("", response_model=SubmissionListResponse)
def list_my_submissions(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[SubmissionsUseCases, Depends(get_submissions_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> SubmissionListResponse:
    page = use_cases.list_my_submissions(actor=current_user, limit=limit, cursor=cursor)
    return SubmissionListResponse(
        items=[SubmissionResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@admin_router.get("", response_model=SubmissionListResponse)
def list_admin_submissions(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[SubmissionsUseCases, Depends(get_submissions_use_cases)],
    submission_status: Annotated[SubmissionStatus, Query(alias="status")] = "pending_review",
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> SubmissionListResponse:
    page = use_cases.list_admin_submissions(
        actor=current_user,
        status=submission_status,
        limit=limit,
        cursor=cursor,
    )
    return SubmissionListResponse(
        items=[SubmissionResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@admin_router.get("/{submission_id}/product-matches", response_model=ProductMatchListResponse)
def list_submission_product_matches(
    submission_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[SubmissionsUseCases, Depends(get_submissions_use_cases)],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> ProductMatchListResponse:
    return ProductMatchListResponse(
        items=[
            product_match_response(match)
            for match in use_cases.list_product_matches(
                actor=current_user,
                submission_id=submission_id,
                limit=limit,
            )
        ]
    )


@admin_router.patch("/{submission_id}", response_model=SubmissionResponse)
def review_submission(
    submission_id: str,
    request: SubmissionReviewRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[SubmissionsUseCases, Depends(get_submissions_use_cases)],
) -> SubmissionResponse:
    return SubmissionResponse.model_validate(
        use_cases.review_submission(
            actor=current_user,
            submission_id=submission_id,
            request=request,
        )
    )


def product_match_response(match: ProductMatch) -> ProductMatchResponse:
    return ProductMatchResponse(
        productId=match.product.id,
        name=match.product.name,
        brand=match.product.brand,
        modelName=match.product.model_name,
        category=match.product.category,
        score=match.score,
        matchedReasons=match.matched_reasons,
    )
