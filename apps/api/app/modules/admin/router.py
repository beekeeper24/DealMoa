from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.db.session import get_session
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import OfferStatusUpdateRequest, OfferStatusUpdateResponse
from app.modules.admin.use_cases import AdminUseCases
from app.modules.auth.router import bearer_scheme, get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser, AuthUseCases
from app.modules.events.repository import DomainEventsRepository
from app.modules.events.use_cases import DomainEventsUseCases
from app.modules.products.repository import ProductRepository

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> AdminUseCases:
    return AdminUseCases(
        admin_repository=AdminRepository(session),
        product_repository=ProductRepository(session),
        domain_events=DomainEventsUseCases(repository=DomainEventsRepository(session)),
    )


def get_current_admin_candidate(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthenticatedUser:
    if credentials is None:
        raise UnauthorizedException()
    return auth_use_cases.get_current_user(credentials.credentials)


@router.patch("/deals/{deal_id}/status", response_model=OfferStatusUpdateResponse)
def update_deal_status(
    deal_id: str,
    request: OfferStatusUpdateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_admin_candidate)],
    use_cases: Annotated[AdminUseCases, Depends(get_admin_use_cases)],
) -> OfferStatusUpdateResponse:
    result = use_cases.update_deal_status(
        actor=current_user,
        deal_id=deal_id,
        request=request,
    )
    return OfferStatusUpdateResponse(
        targetType=result.target_type,
        targetId=result.target_id,
        previousStatus=result.previous_status,
        status=result.status,
        auditLogId=result.audit_log_id,
    )


@router.patch("/auctions/{auction_id}/status", response_model=OfferStatusUpdateResponse)
def update_auction_status(
    auction_id: str,
    request: OfferStatusUpdateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_admin_candidate)],
    use_cases: Annotated[AdminUseCases, Depends(get_admin_use_cases)],
) -> OfferStatusUpdateResponse:
    result = use_cases.update_auction_status(
        actor=current_user,
        auction_id=auction_id,
        request=request,
    )
    return OfferStatusUpdateResponse(
        targetType=result.target_type,
        targetId=result.target_id,
        previousStatus=result.previous_status,
        status=result.status,
        auditLogId=result.audit_log_id,
    )
