from typing import Annotated, cast

from fastapi import APIRouter, Depends, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.db.session import get_session
from app.modules.auth.router import bearer_scheme, get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser, AuthUseCases
from app.modules.discussions.models import ProductDiscussionComment
from app.modules.discussions.repository import DiscussionsRepository
from app.modules.discussions.schemas import (
    DiscussionCommentResponse,
    DiscussionCreateRequest,
    DiscussionListResponse,
    DiscussionModerationRequest,
    DiscussionRiskLevel,
    DiscussionStatus,
    PublicDiscussionCommentResponse,
    PublicDiscussionListResponse,
)
from app.modules.discussions.use_cases import DiscussionsUseCases
from app.modules.products.repository import ProductRepository

router = APIRouter(prefix="/products", tags=["discussions"])
admin_router = APIRouter(prefix="/admin/discussions", tags=["admin-discussions"])


def get_discussions_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> DiscussionsUseCases:
    return DiscussionsUseCases(
        repository=DiscussionsRepository(session),
        product_repository=ProductRepository(session),
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthenticatedUser:
    if credentials is None:
        raise UnauthorizedException()
    return auth_use_cases.get_current_user(credentials.credentials)


@router.get(
    "/{product_id}/discussions",
    response_model=PublicDiscussionListResponse,
    response_model_exclude_none=True,
)
def list_product_discussions(
    product_id: str,
    use_cases: Annotated[DiscussionsUseCases, Depends(get_discussions_use_cases)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> PublicDiscussionListResponse:
    page = use_cases.list_public_comments(product_id=product_id, limit=limit, cursor=cursor)
    return PublicDiscussionListResponse(
        items=[public_response(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@router.post(
    "/{product_id}/discussions",
    response_model=DiscussionCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_discussion(
    product_id: str,
    request: DiscussionCreateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[DiscussionsUseCases, Depends(get_discussions_use_cases)],
) -> DiscussionCommentResponse:
    return discussion_response(
        use_cases.create_comment(actor=current_user, product_id=product_id, request=request)
    )


@admin_router.get("", response_model=DiscussionListResponse)
def list_admin_discussions(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[DiscussionsUseCases, Depends(get_discussions_use_cases)],
    discussion_status: Annotated[DiscussionStatus, Query(alias="status")] = "visible",
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> DiscussionListResponse:
    page = use_cases.list_admin_comments(
        actor=current_user,
        status=discussion_status,
        limit=limit,
        cursor=cursor,
    )
    return DiscussionListResponse(
        items=[discussion_response(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@admin_router.patch("/{comment_id}", response_model=DiscussionCommentResponse)
def moderate_discussion(
    comment_id: str,
    request: DiscussionModerationRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[DiscussionsUseCases, Depends(get_discussions_use_cases)],
) -> DiscussionCommentResponse:
    return discussion_response(
        use_cases.moderate_comment(
            actor=current_user,
            comment_id=comment_id,
            request=request,
        )
    )


def public_response(comment: ProductDiscussionComment) -> PublicDiscussionCommentResponse:
    return PublicDiscussionCommentResponse(
        id=comment.id,
        productId=comment.product_id,
        userNickname=comment.user.nickname or "알 수 없는 사용자",
        body=comment.body,
        createdAt=comment.created_at,
        updatedAt=comment.updated_at,
    )


def discussion_response(comment: ProductDiscussionComment) -> DiscussionCommentResponse:
    return DiscussionCommentResponse(
        id=comment.id,
        productId=comment.product_id,
        userId=comment.user_id,
        userNickname=comment.user.nickname or "알 수 없는 사용자",
        body=comment.body,
        status=cast(DiscussionStatus, comment.status),
        riskScore=comment.moderation_risk_score,
        riskLevel=cast(DiscussionRiskLevel, comment.moderation_risk_level),
        riskReasons=comment.moderation_risk_reasons_json,
        moderatedByUserId=comment.moderated_by_user_id,
        moderationNote=comment.moderation_note,
        moderatedAt=comment.moderated_at,
        createdAt=comment.created_at,
        updatedAt=comment.updated_at,
    )
