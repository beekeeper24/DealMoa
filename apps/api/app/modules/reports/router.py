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
from app.modules.reports.repository import ReportsRepository
from app.modules.reports.schemas import (
    ReportCreateRequest,
    ReportListResponse,
    ReportResponse,
    ReportReviewRequest,
    ReportStatus,
)
from app.modules.reports.use_cases import ReportsUseCases

router = APIRouter(prefix="/reports", tags=["reports"])
admin_router = APIRouter(prefix="/admin/reports", tags=["admin-reports"])


def get_reports_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> ReportsUseCases:
    return ReportsUseCases(
        repository=ReportsRepository(session),
        domain_events=DomainEventsUseCases(repository=DomainEventsRepository(session)),
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthenticatedUser:
    if credentials is None:
        raise UnauthorizedException()
    return auth_use_cases.get_current_user(credentials.credentials)


@router.post(
    "/deals/{deal_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def report_deal(
    deal_id: str,
    request: ReportCreateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[ReportsUseCases, Depends(get_reports_use_cases)],
) -> ReportResponse:
    report = use_cases.report_deal(actor=current_user, deal_id=deal_id, request=request)
    return ReportResponse.model_validate(report)


@router.post(
    "/auctions/{auction_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def report_auction(
    auction_id: str,
    request: ReportCreateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[ReportsUseCases, Depends(get_reports_use_cases)],
) -> ReportResponse:
    report = use_cases.report_auction(actor=current_user, auction_id=auction_id, request=request)
    return ReportResponse.model_validate(report)


@admin_router.get("", response_model=ReportListResponse)
def list_reports(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[ReportsUseCases, Depends(get_reports_use_cases)],
    report_status: Annotated[ReportStatus, Query(alias="status")] = "open",
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> ReportListResponse:
    page = use_cases.list_reports(
        actor=current_user,
        status=report_status,
        limit=limit,
        cursor=cursor,
    )
    return ReportListResponse(
        items=[ReportResponse.model_validate(item) for item in page.items],
        nextCursor=page.next_cursor,
    )


@admin_router.patch("/{report_id}", response_model=ReportResponse)
def review_report(
    report_id: str,
    request: ReportReviewRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    use_cases: Annotated[ReportsUseCases, Depends(get_reports_use_cases)],
) -> ReportResponse:
    report = use_cases.review_report(
        actor=current_user,
        report_id=report_id,
        request=request,
    )
    return ReportResponse.model_validate(report)
